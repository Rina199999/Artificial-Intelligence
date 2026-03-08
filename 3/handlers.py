import requests

WEATHER_TRANSLATIONS = {
    "Partly cloudy": "Переменная облачность",
    "Cloudy": "Облачно",
    "Overcast": "Пасмурно",
    "Sunny": "Ясно",
    "Clear": "Ясно",
    "Rain": "Дождь",
    "Light rain": "Небольшой дождь",
    "Snow": "Снег",
    "Light snow": "Небольшой снег",
    "Light Freezing Rain ": "Легкий ледяной дождь",
    "Light Snow, Snow Shower": "Небольшой кратковременный снегопад",
    "Mist": "Туман",
    "Patchy rain nearby": "Мелкий дождь"
}


def get_weather(city):
    target_city = city if city else "Nizhny Novgorod"

    API_KEY = "ae7074060ac6115686a0baab31843287"
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
    city = match.group(1) #
    return get_weather(city) #

def handle_greeting(match=None):
    return "Здравствуйте! Чем могу помочь?"

def handle_addition(match):
    try:
        a = float(match.group(1))
        b = float(match.group(2))
        return f"Результат: {a + b}"
    except:
        return "Не удалось посчитать."