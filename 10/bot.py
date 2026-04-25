import torch
import spacy
import json
import logger
import patterns
import handlers
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from datetime import datetime
import voice
import os

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

nlp = spacy.load("ru_core_news_md")
MODEL_PATH = "intent_model"


class DialogState:
    START = "start"
    WAIT_CITY = "wait_city"


class ChatBot:
    def __init__(self):
        self.name = logger.load_user_name()
        self.patterns = patterns.get_patterns(self)
        self.state = logger.load_state() or DialogState.START

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
            self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
            self.model.eval()
            with open(f"{MODEL_PATH}/label_map.json", "r") as f:
                self.label_map = {int(k): v for k, v in json.load(f).items()}
        except Exception as e:
            print(f"Ошибка загрузки BERT: {e}. Сначала обучите модель!")
            self.model = None

    def predict_intent(self, text):
        if not self.model:
            return "unknown"

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)

        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        conf, pred_idx = torch.max(probs, dim=1)

        intent = self.label_map.get(pred_idx.item(), "unknown")
        print(f"DEBUG: '{text}' -> BERT: {intent} (conf: {conf.item():.2f})")

        return intent if conf.item() > 0.2 else "unknown"

    def extract_city(self, text):
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:
                return ent.lemma_
        return None

    def update_state(self, new_state):
        self.state = new_state
        logger.save_state(new_state)

    def set_name(self, match):
        new_name = match.group(1)
        self.name = new_name
        logger.save_user_name(new_name)
        return f"Приятно познакомиться, {self.name}!"

    def process(self, message: str):
        for pattern, handler in self.patterns:
            match = pattern.search(message)
            if match:
                res = handler(match)
                if res == "EXIT_SIGNAL":
                    return res
                return res

        if self.state == DialogState.WAIT_CITY:
            city = self.extract_city(message) or message.strip()
            self.update_state(DialogState.START)
            return handlers.get_weather(city)

        intent = self.predict_intent(message)

        if intent == "weather":
            city = self.extract_city(message)
            if city:
                return handlers.get_weather(city)
            else:
                self.update_state(DialogState.WAIT_CITY)
                return "В каком городе вас интересует погода?"

        elif intent == "time":
            return handlers.get_time_or_date("time")

        elif intent == "date":
            return handlers.get_time_or_date("date")

        elif intent == "help":
            return handlers.get_help()

        elif intent == "smalltalk":
            return handlers.handle_smalltalk()

        elif intent == "greeting":
            return f"Привет, {self.name or 'друг'}! Чем могу помочь?"

        elif intent == "thanks":
            return handlers.handle_thanks()

        elif intent == "goodbye":
            return "EXIT_SIGNAL"

        return "Я не совсем понял. Можете спросить про погоду?"


if __name__ == "__main__":
    print("=" * 50)
    print("Чат-бот с голосовым управлением")
    print("=" * 50)

    bot = ChatBot()
    print(f"Бот запущен. Текущий статус: {bot.state}")
    print("Бот готов к работе. Используйте голосовой ввод.\n")
    print("Инструкция:")
    print("- Говорите четко в микрофон после сигнала 'Слушаю...'")
    print("- Скажите 'пока' или 'до свидания' для выхода")
    print("-" * 50 + "\n")

    while True:
        try:
            user_input = voice.listen()

            if not user_input or len(user_input.strip()) == 0:
                print("⚠️ Не удалось распознать речь. Попробуйте еще раз громче и четче.\n")
                continue

            print(f"📝 Вы сказали: {user_input}")

            response = bot.process(user_input)

            if response == "EXIT_SIGNAL":
                final_msg = "До свидания! Было приятно пообщаться."
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Бот: {final_msg}")
                voice.speak(final_msg)
                break

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Бот: {response}\n")

            voice.speak(response)

            logger.log_message(user_input, response, bot.state)

        except KeyboardInterrupt:
            print("\n\n👋 Программа прервана пользователем")
            voice.speak("До свидания!")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback

            traceback.print_exc()
            continue