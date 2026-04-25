import requests
from datetime import datetime

WEATHER_TRANSLATIONS = {
    "Partly cloudy": "Переменная облачность",
    "Partly Cloudy ": "Переменная облачность",
    "Cloudy": "Облачно",
    "Overcast": "Пасмурно",
    "Sunny": "Ясно",
    "Clear": "Ясно",
    "Clear ": "Ясно",
    "Rain": "Дождь",
    "Light rain": "Небольшой дождь",
    "Light rain ": "Небольшой дождь",
    "Snow": "Снег",
    "Light snow": "Небольшой снег",
    "Light snow ": "Небольшой снег",
    "Light Freezing Rain ": "Легкий ледяной дождь",
    "Light Freezing Rain": "Легкий ледяной дождь",
    "Light Snow, Snow Shower": "Небольшой кратковременный снегопад",
    "Mist": "Туман",
    "Patchy rain nearby": "Мелкий дождь"
}


def get_weather(city):
    target_city = city if city else "Nizhny Novgorod"

    API_KEY = "938681a5507b1b69d60017c47d2c6d28"
    url = f"http://api.weatherstack.com/current?access_key={API_KEY}&query={target_city}"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if "current" in data:
            temp = data["current"]["temperature"]
            wind = data["current"]["wind_speed"]
            desc_en = data["current"]["weather_descriptions"][0]

            desc_ru = WEATHER_TRANSLATIONS.get(desc_en, desc_en)

            display_city = "Нижнем Новгороде" if target_city == "Nizhny Novgorod" else target_city
            return f"Погода в городе {display_city}: {desc_ru}. Температура: {temp}°C, ветер: {wind} км/ч."
        else:
            return "Не удалось найти такой город."
    except:
        return "Ошибка связи с сервером погоды."


def handle_weather(match):
    city = match.group(1)
    return get_weather(city)

def handle_greeting(match=None):
    return "Здравствуйте! Чем могу помочь?"

def handle_addition(match):
    try:
        a = float(match.group(1))
        b = float(match.group(2))
        return f"Результат: {a + b}"
    except:
        return "Не удалось посчитать."

def get_time_or_date(mode="time"):
    now = datetime.now()
    if mode == "time":
        return f"Сейчас {now.strftime('%H:%M')}."
    return f"Сегодня {now.strftime('%d.%m.%Y')}."

def get_help():
    return (
        "Вот что я умею:\n"
        "1. Прогноз погоды (спросите: 'Какая погода в Лондоне?')\n"
        "2. Математика (напишите: '5 + 7')\n"
        "3. Время и дата\n"
        "4. Могу просто поболтать!"
    )

def handle_smalltalk():
    return "У меня все отлично, я ведь просто бот. Надеюсь, у тебя тоже всё в порядке."

def handle_thanks():
    return "Всегда пожалуйста!"