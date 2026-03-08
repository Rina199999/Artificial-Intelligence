import re
import handlers

def get_patterns(bot_instance):
    return [
        (re.compile(r"^(привет|здравствуйте|добрый день)", re.IGNORECASE), handlers.handle_greeting),
        (re.compile(r"^(пока|до свидания)", re.IGNORECASE), lambda m: "EXIT_SIGNAL"),
        (re.compile(r"погода", re.IGNORECASE), handlers.handle_weather),
        (re.compile(r"(\d+)\s*\+\s*(\d+)", re.IGNORECASE), handlers.handle_addition),
        (re.compile(r"меня зовут ([а-яА-Яa-zA-Z]+)", re.IGNORECASE), bot_instance.set_name),
    ]