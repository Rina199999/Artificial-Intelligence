from transformers import VitsModel, AutoTokenizer
import torch
import soundfile as sf
import re
import whisper
import numpy as np
from scipy.io.wavfile import write, read
import pyaudio
import wave
import os
import time

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"


class RussianTTS:
    def __init__(self):
        print("Загрузка модели TTS...")
        model_name = "joefox/tts_vits_ru_hf"
        self.model = VitsModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.sample_rate = self.model.config.sampling_rate

        self.digits = {
            '0': 'ноль', '1': 'один', '2': 'два', '3': 'три', '4': 'четыре',
            '5': 'пять', '6': 'шесть', '7': 'семь', '8': 'восемь', '9': 'девять'
        }

        self.tens = {
            '10': 'десять', '11': 'одиннадцать', '12': 'двенадцать',
            '13': 'тринадцать', '14': 'четырнадцать', '15': 'пятнадцать',
            '16': 'шестнадцать', '17': 'семнадцать', '18': 'восемнадцать',
            '19': 'девятнадцать', '20': 'двадцать', '30': 'тридцать',
            '40': 'сорок', '50': 'пятьдесят', '60': 'шестьдесят',
            '70': 'семьдесят', '80': 'восемьдесят', '90': 'девяносто'
        }

        self.hundreds = {
            '100': 'сто', '200': 'двести', '300': 'триста',
            '400': 'четыреста', '500': 'пятьсот', '600': 'шестьсот',
            '700': 'семьсот', '800': 'восемьсот', '900': 'девятьсот'
        }
        print("Модель TTS загружена!")

    def number_to_words(self, num_str):
        try:
            num = int(num_str)
            if num < 0:
                return "минус " + self.number_to_words(str(abs(num)))

            if num == 0:
                return "ноль"

            if num <= 9:
                return self.digits[num_str]

            if 10 <= num <= 20:
                return self.tens[str(num)]

            if 20 < num < 100:
                tens_num = (num // 10) * 10
                units_num = num % 10
                tens_word = self.tens[str(tens_num)]
                if units_num == 0:
                    return tens_word
                units_word = self.digits[str(units_num)]
                return f"{tens_word} {units_word}"

            if 100 <= num < 1000:
                hundreds_num = (num // 100) * 100
                remainder = num % 100
                hundreds_word = self.hundreds[str(hundreds_num)]
                if remainder == 0:
                    return hundreds_word
                remainder_word = self.number_to_words(str(remainder))
                return f"{hundreds_word} {remainder_word}"

            return num_str

        except ValueError:
            return num_str

    def normalize_text(self, text):
        original = text

        replacements = {
            '°C': ' градусов Цельсия',
            '°': ' градусов',
            'км/ч': ' километров в час',
            'km/h': ' километров в час',
            'м/с': ' метров в секунду',
            'м/c': ' метров в секунду',
            '%': ' процентов',
            '+': ' плюс '
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        def replace_float(match):
            num = match.group(0)
            if '.' in num:
                parts = num.split('.')
                integer_part = parts[0]
                fractional_part = parts[1]

                if integer_part == '0':
                    integer_words = "ноль"
                else:
                    integer_words = self.number_to_words(integer_part)

                fractional_words = ' '.join([self.digits[d] for d in fractional_part])

                if integer_part == '1':
                    whole_word = "целая"
                elif integer_part in ['2', '3', '4']:
                    whole_word = "целых"
                else:
                    whole_word = "целых"

                return f"{integer_words} {whole_word} {fractional_words}"
            return num

        text = re.sub(r'\d+\.\d+', replace_float, text)

        def replace_int(match):
            num = match.group(0)
            if re.search(r'\d+\.\d+', num):
                return num
            return self.number_to_words(num)

        text = re.sub(r'\b([1-9][0-9]{0,2})\b', replace_int, text)

        def replace_range(match):
            numbers = match.group(0).split('-')
            if len(numbers) == 2:
                num1 = self.number_to_words(numbers[0])
                num2 = self.number_to_words(numbers[1])
                if numbers[0].endswith(('2', '3', '4')) and not numbers[0].endswith(('12', '13', '14')):
                    num1 = num1.replace('два', 'двух').replace('три', 'трёх').replace('четыре', 'четырёх')
                    num1 = num1.replace('один', 'одного')
                elif numbers[0].endswith('1') and not numbers[0].endswith('11'):
                    num1 = num1.replace('один', 'одного')
                else:
                    num1 = num1 + 'и' if num1.endswith('ь') else num1 + 'а'
                return f"с {num1} до {num2}"
            return match.group(0)

        text = re.sub(r'\d+-\d+', replace_range, text)

        text = re.sub(r'\s+', ' ', text)

        if original != text:
            print(f"📝 Нормализация:")
            print(f"   Было: {original}")
            print(f"   Стало: {text}")

        return text.strip()

    def speak(self, text, output_file="output.wav", speaker_id=3):
        try:
            normalized_text = self.normalize_text(text)
            print(f"🎤 Произносится: {normalized_text}")

            normalized_text = normalized_text.lower()
            inputs = self.tokenizer(normalized_text, return_tensors="pt")
            inputs['speaker_id'] = speaker_id

            with torch.no_grad():
                output = self.model(**inputs).waveform

            audio = output[0].cpu().numpy()
            sf.write(output_file, audio, self.sample_rate)

            self._play_audio_pyaudio(output_file)

            return output_file
        except Exception as e:
            print(f"❌ Ошибка TTS: {e}")
            return None

    def _play_audio_pyaudio(self, filename):
        try:
            wf = wave.open(filename, 'rb')

            p = pyaudio.PyAudio()

            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)

            data = wf.readframes(1024)
            while data:
                stream.write(data)
                data = wf.readframes(1024)

            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()
        except Exception as e:
            print(f"❌ Ошибка воспроизведения: {e}")


def record_audio_pyaudio(filename="input.wav", seconds=4, fs=16000):
    try:
        chunk = 1024
        format = pyaudio.paInt16
        channels = 1

        p = pyaudio.PyAudio()

        stream = p.open(format=format,
                        channels=channels,
                        rate=fs,
                        input=True,
                        frames_per_buffer=chunk)

        print("🎤 Слушаю... (говорите громко и четко)")
        frames = []

        for i in range(0, int(fs / chunk * seconds)):
            data = stream.read(chunk)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(filename, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format))
        wf.setframerate(fs)
        wf.writeframes(b''.join(frames))
        wf.close()

        print("✅ Запись завершена!")
        return filename
    except Exception as e:
        print(f"❌ Ошибка записи: {e}")
        return None


def load_audio_direct(filename):
    try:
        sample_rate, audio_data = read(filename)

        if audio_data.dtype == np.int16:
            audio = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            audio = audio_data.astype(np.float32) / 2147483648.0
        else:
            audio = audio_data.astype(np.float32)

        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        return audio
    except Exception as e:
        print(f"❌ Ошибка чтения аудио: {e}")
        return None


print("Загрузка моделей...")
tts = RussianTTS()
whisper_model = whisper.load_model("base")
print("Все модели загружены!")


def speech_to_text(filename="input.wav"):
    try:
        audio = load_audio_direct(filename)
        if audio is None:
            return ""

        result = whisper_model.transcribe(audio, language="ru", fp16=False)
        raw_text = result["text"]

        clean_text = raw_text.lower().strip()
        clean_text = re.sub(r"[^\w\sа-яё0-9\+\-\*\/\.\,\?\!]", "", clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        print(f"👂 Распознано: {clean_text}")
        return clean_text
    except Exception as e:
        print(f"❌ Ошибка распознавания: {e}")
        return ""


def listen():
    record_audio_pyaudio()
    return speech_to_text()


def speak(text):
    return tts.speak(text)