from transformers import VitsModel, AutoTokenizer
import torch
import soundfile as sf
import sounddevice as sd
import re


class RussianTTS:
    def __init__(self):
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
        normalized_text = self.normalize_text(text)

        print(f"🎤 Произносится: {normalized_text}")

        normalized_text = normalized_text.lower()
        inputs = self.tokenizer(normalized_text, return_tensors="pt")
        inputs['speaker_id'] = speaker_id

        with torch.no_grad():
            output = self.model(**inputs).waveform

        audio = output[0].cpu().numpy()
        sf.write(output_file, audio, self.sample_rate)

        data, fs = sf.read(output_file)
        sd.play(data, fs)
        sd.wait()
        return output_file

tts = RussianTTS()

def speak(text):
    return tts.speak(text)