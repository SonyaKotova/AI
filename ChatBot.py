import datetime
import re
import random
import locale
import webbrowser
import requests

API_KEY = "f62350d6ff8c087ec53d1479dab00ade"

locale.setlocale(
    category=locale.LC_ALL,
    locale="Russian"
)

time = datetime.datetime.now().strftime("%H:%M:%S")
day = datetime.datetime.now().strftime("%A")
date = datetime.datetime.now().strftime("%a %d.%m.%y")

# Определяем словарь шаблонов и ответов
responses = {
    r"привет": "Привет! Как я могу помочь?",
    r"здравствуй": "Добрый день! Как я могу помочь?",
    r"как тебя зовут\??": "Я бот-помощник!",
    r"что ты умеешь\??": [
        "Я умею отвечать на простые вопросы, подскажу тебе сегодняшнюю дату и время, "
        "а также решу простейшие арифметические выражения. Попробуй спросить: 'Как тебя зовут?'",
        "Мои возможности ограничены, но я могу помочь с простыми задачами"
    ],
    r"который час\??": f"Сейчас {time}",
    r"сколько сейчас времени\??": f"Сейчас уже {time}",
    r"какой сегодня день недели\??": f"{day}",
    r"какое сегодня число\??": f"Сегодня {date}",
    r"какая сегодня дата\??": f"Сегодня {date}",
    #r"какая сегодня погода\??": "Я не синоптик",
    r"как дела\??": [
        "Всё чудесно! За окном весна!",
        "Спасибо за вопрос! У меня все хорошо!",
        "Я просто программа, я просто программа...",
        "Неплохо, а у тебя как дела?"
    ],
    r"все хорошо": "Чудесно!",
    r"какое твое любимое время года\??": [
        "Я люблю лето - тепло, птички поют",
        "Обожаю осень! Осенняя листва - это взрыв ярких красок!",
        "Мое любимое время года - зима. Череда праздников, это семейное время.",
        "Весна. Это время расцвета природы - все оживает, просыпается после зимы."
    ]
}

def calculate(expression):
    try:
        expression = expression.replace(" ", "")
        if not re.fullmatch(r"\d+[\+\-\*/]\d+", expression):
            return "Некорректное выражение"
        result = eval(expression)
        return str(result)
    except ZeroDivisionError:
        return "Ошибка: деление на ноль"
    except Exception:
        return "Ошибка в вычислении"

def search_web(query):
    url = f"https://www.google.com/search?q={query.replace('','+')}"
    webbrowser.open(url)
    return random.choice([
        f"Ищу в интернете: {query}",
        f"Запрос: {query} принят в обработку",
        f"Идет поиск: {query}"
    ])

def get_weather(city):
    url_w = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
    response = requests.get(url_w)
    if response.status_code == 200:
        data = response.json()
        temp = data["main"]["temp"]
        weather_desc = data["weather"][0]["description"]
        return f"В городе {city} сейчас {weather_desc} при температуре {temp} C."
    else:
        return "Не удалось получить информацию о погоде."

def log_dialog(user_input, bot_response):
    with open("chat_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"Пользователь: {user_input}\n")
        log_file.write(f"Бот: {bot_response}\n")
        log_file.write("-" * 40 + "\n")

def chatbot_response(text):
    text = text.lower().strip()

    match = re.search(r"(?:поиск|найди)\s+(.+)", text)
    if match:
        query = match.group(1)
        return search_web(query)

    match = re.search((r"(?:погода в|какая погода в)\s+(.+)"), text)
    if match:
        city = match.group(1)
        return get_weather(city)

    # Проверяем шаблонные ответы
    for pattern, reply in responses.items():
        if re.search(pattern, text):
            # Если ответ список - берем случайный, иначе берем как есть
            if isinstance(reply, list):
                return random.choice(reply)
            else:
                return reply

    # Проверяем команды на вычисление
    match = re.search(r"(?:вычисли|посчитай)\s*([\d+\-*/ ]+)", text)
    if match:
        return calculate(match.group(1))

    # Если пользователь ввел просто арифметическое выражение
    if re.fullmatch(r"[\d+\-*/ ]+", text):
        return calculate(text)

    # Рандомный ответ на непонятный запрос
    return random.choice(["Я не понял вопрос.", "Попробуйте перефразировать."])

if __name__ == "__main__":
    with open("chat_log.txt", "w", encoding="utf-8") as log_file:
        log_file.write("-" * 40 + "\n")
        
    print("Введите 'выход' для завершения диалога.")
    while True:
        user_input = input("Вы: ")
        if user_input.lower() == "выход":
            farewell = random.choice(["До свидания!", "Хорошего дня!"])
            print("Бот:", farewell)
            with open("chat_log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"Пользователь: {user_input}\n")
                log_file.write(f"Бот: {farewell}\n")
                log_file.write("-" * 40 + "\n")
            break
        bot_reply = chatbot_response(user_input)
        print("Бот:", bot_reply)
        # Логируем диалог
        log_dialog(user_input, bot_reply)
