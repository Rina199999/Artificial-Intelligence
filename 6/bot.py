import spacy
from datetime import datetime
import patterns
import logger
import handlers
import joblib

nlp = spacy.load("ru_core_news_md")

class DialogState:
    START = "start"
    WAIT_CITY = "wait_city"

class ChatBot:
    def __init__(self):
        self.name = logger.load_user_name()
        self.patterns = patterns.get_patterns(self)
        saved_state = logger.load_state()
        if saved_state:
            self.state = saved_state
        else:
            self.state = DialogState.START

        try:
            self.model = joblib.load("bot_embeddings_model.joblib")
        except:
            print("Ошибка: Файл модели не найден. Запустите train_model.py")
            self.model = None

    def preprocess(self, text):
        doc = nlp(text.lower())
        return " ".join([t.lemma_ for t in doc if not t.is_stop and not t.is_punct])

    def predict_intent(self, text):
        if not self.model: return "unknown"
        vector = nlp(text).vector.reshape(1, -1)

        intent = self.model.predict(vector)[0]
        proba = max(self.model.predict_proba(vector)[0])

        print(f"DEBUG: Текст: '{text}' -> Интент: {intent} (Уверенность: {proba:.2f})")
        return intent if proba > 0.3 else "unknown"

    def update_state(self, new_state):
        self.state = new_state
        logger.save_state(new_state)

    def set_name(self, match):
        new_name = match.group(1)
        self.name = new_name
        logger.save_user_name(new_name)
        return f"Приятно познакомиться, {self.name}!"

    def extract_city(self, text):
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:
                return ent.text.capitalize()
        return None

    def process(self, message: str):
        response = ""

        if self.state == DialogState.WAIT_CITY:
            self.update_state(DialogState.START)
            response = handlers.get_weather(message.strip())
        else:
            intent = self.predict_intent(message)

            if intent == "weather":
                city = self.extract_city(message)
                if city:
                    response = handlers.get_weather(city)
                else:
                    self.update_state(DialogState.WAIT_CITY)
                    response = "В каком городе вас интересует погода?"

            elif intent == "greeting":
                response = "Привет! Чем я могу вам помочь?"

            else:
                found_pattern = False
                for pattern, handler in self.patterns:
                    match = pattern.search(message)
                    if match:
                        response = handler(match)
                        found_pattern = True
                        break

                if not found_pattern:
                    response = "Я не совсем понял. Можете спросить про погоду?"

        logger.log_message(message, response, self.state)
        return response

    def update_state(self, new_state):
        self.state = new_state
        logger.save_state(new_state)


if __name__ == "__main__":
    bot = ChatBot()
    start_time = datetime.now().strftime('%H:%M:%S')

    if bot.name:
        print(f"[{start_time}] Бот: Привет, {bot.name}! Я готов.")
    else:
        print(f"[{start_time}] Бот запущен. Как мне вас называть?")

    while True:
        user_input = input("Вы: ")
        if user_input.lower() in ["пока", "выход"]:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Бот: До свидания!")
            break

        response = bot.process(user_input)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Бот: {response}")

        logger.log_message(user_input, response, bot.state)