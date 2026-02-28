import string
from datetime import datetime
import patterns
import logger


class ChatBot:
    def __init__(self):
        self.name = logger.load_user_name()
        self.patterns = patterns.get_patterns(self)

    def set_name(self, match):
        new_name = match.group(1)
        if self.name and self.name.lower() == new_name.lower():
            return f"Я уже знаю, что вас зовут {self.name}!"

        self.name = new_name
        logger.save_user_name(new_name)
        return f"Приятно познакомиться, {self.name}!"

    def process(self, message: str):
        punct = string.punctuation.replace('+', '')
        clean_msg = message.lower().strip().translate(str.maketrans('', '', punct))

        for pattern, handler in self.patterns:
            match = pattern.search(clean_msg)
            if match:
                return handler(match)
        return "Я не понимаю запрос."


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