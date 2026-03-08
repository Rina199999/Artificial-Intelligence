import spacy
from datetime import datetime
import patterns
import logger
import handlers

nlp = spacy.load("ru_core_news_sm")


class ChatBot:
    def __init__(self):
        self.name = logger.load_user_name()
        self.patterns = patterns.get_patterns(self)

    def set_name(self, match):
        new_name = match.group(1)
        self.name = new_name
        logger.save_user_name(new_name)
        return f"Приятно познакомиться, {self.name}!"

    def extract_city(self, text):
        doc = nlp(text)
        for token in doc:
            if token.ent_type_ in ["GPE", "LOC"]:
                return token.lemma_

        words = text.split()
        for word in words:
            clean_word = word.strip(".,!?")
            if clean_word.lower() not in ["я", "привет", "добрый", "здравствуйте", "погода", "в"]:
                return clean_word.capitalize()
        return None

    def process(self, message: str):
        msg_lower = message.lower()

        weather_triggers = ['погод', 'температур', 'градус', 'прогноз']

        if any(trigger in msg_lower for trigger in weather_triggers):

            city = self.extract_city(message)

            if city:

                result = handlers.get_weather(city)
                return result
            else:

                return handlers.get_weather("Nizhny Novgorod")
        return "Я не понимаю запрос. Попробуйте спросить о погоде."


if __name__ == "__main__":
    bot = ChatBot()

    start_time = datetime.now().strftime('%H:%M:%S')
    if bot.name:
        print(f"[{start_time}] Бот: Привет, {bot.name}! Я готов к работе.")
    else:
        print(f"[{start_time}] Бот запущен. Как мне вас называть?")

    while True:
        user_input = input("Вы: ")
        response = bot.process(user_input)

        if response == "EXIT_SIGNAL":
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Бот: До свидания!")
            break

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Бот: {response}")
        logger.log_message(user_input, response)