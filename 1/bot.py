import string
from datetime import datetime
import patterns
from logger import log_message


class ChatBot:
    def __init__(self):
        self.name = None
        self.patterns = patterns.get_patterns(self)

    def set_name(self, match):
        self.name = match.group(1)
        return f"Приятно познакомиться, {self.name}!"

    def process(self, message: str):
        punctuation_to_remove = string.punctuation.replace('+', '')
        clean_message = message.lower().strip().translate(str.maketrans('', '', punctuation_to_remove))

        for pattern, handler in self.patterns:
            match = pattern.search(clean_message)
            if match:
                return handler(match)

        return "Я не понимаю запрос."


if __name__ == "__main__":
    bot = ChatBot()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Бот запущен.")

    while True:
        try:
            user_input = input("Вы: ")
            if user_input.lower() in ['выход', 'exit', 'quit']:
                break

            response = bot.process(user_input)

            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"[{current_time}] Бот: {response}")

            log_message(user_input, response)

        except KeyboardInterrupt:
            break