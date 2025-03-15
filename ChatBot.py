import datetime
import re
import random
import locale

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
    r"что ты умеешь\??": "Я умею отвечать на простые вопросы, подскажу тебе сегодняшнюю дату и время, "
                        "а также решу простейшие арифметические выражения. Попробуй спросить: 'Как тебя зовут?'",
    r"который час\??": f"Сейчас {time}",
    r"сколько сейчас времени\??": f"Сейчас уже {time}",
    r"какой сегодня день недели\??": f"{day}",
    r"какое сегодня число\??": f"Сегодня {date}",
    r"какая сегодня дата\??": f"Сегодня {date}",
    r"какая сегодня погода\??": "Я не синоптик",
    r"как дела\??": "Всё чудесно! За окном весна!"
}

def calculate(expression):
    try:
        # Заменяем пробелы, если есть, и проверяем корректность выражения
        expression = expression.replace(" ", "")
        if not re.fullmatch(r"\d+[\+\-\*/]\d+", expression):
            return "Некорректное выражение"

        result = eval(expression)
        return str(result)
    except ZeroDivisionError:
        return "Ошибка: деление на ноль"
    except Exception:
        return "Ошибка в вычислении"

def chatbot_response(text):
    text = text.lower().strip()  # Приведение к нижнему регистру и удаление лишних пробелов

    # Проверяем шаблонные ответы
    for pattern, response in responses.items():
        if re.search(pattern, text):
            return response

    # Проверяем, если сообщение содержит "вычисли" или "посчитай", затем ищем выражение
    match = re.search(r"(?:вычисли|посчитай)\s*([\d+\-*/ ]+)", text)
    if match:
        return calculate(match.group(1))

    # Проверяем, если пользователь ввел только арифметическое выражение
    if re.fullmatch(r"[\d+\-*/ ]+", text):
        return calculate(text)

    return random.choice(["Я не понял вопрос.", "Попробуйте перефразировать."])


if __name__ == "__main__":
    print("Введите 'выход' для завершения диалога.")
    while True:
        user_input = input("Вы: ")
        if user_input.lower() == "выход":
            print("Бот:", random.choice(["До свидания!", "Хорошего дня!"]))
            break
        print("Бот:", chatbot_response(user_input))