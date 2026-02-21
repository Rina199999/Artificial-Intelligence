def handle_greeting(match=None):
    return "Здравствуйте! Чем могу помочь?"

def handle_farewell(match=None):
    return "До свидания!"

def handle_weather(match):
    city = match.group(1)
    return f"Погода в городе {city}: солнечно."

def handle_addition(match):
    try:
        a = float(match.group(1))
        b = float(match.group(2))
        return f"Результат: {a + b}"
    except (ValueError, IndexError):
        return "Ошибка в расчетах."