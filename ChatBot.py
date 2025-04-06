import spacy
import datetime
import re
import random
import webbrowser
import requests
from textblob import TextBlob
from googletrans import Translator
import locale
locale.setlocale(locale.LC_TIME, 'rus_rus')

# Инициализация
translator = Translator()
API_KEY = "f62350d6ff8c087ec53d1479dab00ade"
nlp = spacy.load("ru_core_news_sm")

# Логирование
def log_interaction(user_input, bot_response):
    with open("chat_log.txt", "a", encoding="utf-8") as f:
        f.write(f"Пользователь: {user_input}\nБот: {bot_response}\n{'='*50}\n")

def lemmatize_text(text):
    doc = nlp(text)
    lemmas = [token.lemma_.lower() for token in doc if not token.is_punct and not token.is_space]
    return " ".join(lemmas)

# Словарь интентов
INTENTS = {
    "translate" : {
        "patterns": [
            r"переведи ['\"]?(.+?)['\"]? на английский",
            r"перевод ['\"]?(.+?)['\"]? на английский",
            r"как будет ['\"]?(.+?)['\"]? по-английски"
        ],
        "handler": lambda text: f"Перевод: {translator.translate(text, dest='en').text}"
    },
    "echo" : {
        "patterns": [r"\bскажи\b(.+)", r"повтори (.+)"],
        "handler": lambda text: f"Вы сказали: {text}"
    },
    "greeting" : {
        "patterns": [
            r"(?:привет|здравствуй|хай|\bдобрый день\b|\bдоброе утро\b|\bдобрый вечер\b|салют)",
            r"(?:привет|здравствуй)[, ]*бот"
            ],
        "responses": ["Привет! Как я могу помочь?", "Здравствуй! Как настроение?", "Приветики!"]
    },
    "goodbye" : {
        "patterns": [
            r"(?:пока|до свидания|выход|до встречи|прощай|\bвсего доброго\b|завершить)",
            r"(?:пока|до свидания)[, ]*бот"
        ],
        "responses": ["До встречи!", "Хорошего дня!", "Пока", "Пока-пока"],
        "terminate": True
    },
    "help" : {
        "patterns": [r"\bпомощь\b", r"\bкоманды\b", r"\bчто ты умеешь\b", r"\bкакие у тебя есть функции\b", r"\bчто ты можешь\b"],
        "responses": [
            "Я могу: рассказать анекдот, показать погоду, перевести текст, "
            "посчитать пример и сказать время. Просто спросите!",
            "Я умею немного: пообщаться, посчитать и подсказать!"
        ]
    },
    "season": {
        "patterns": [r"какое твое любимое время года", r"любимое время года"],
        "responses": [
            "Я люблю лето - тепло, птички поют",
            "Обожаю осень! Осенняя листва - это взрыв ярких красок!",
            "Мое любимое время года - зима. Череда праздников, это семейное время."
        ]
    },
    "weather" : {
        "patterns": [
            r"погода в ([\w-]+)",
            r"прогноз погоды для ([\w-]+)",
            r"прогноз погоды в ([\w-]+)"
        ],
        "handler": lambda text: get_weather(analyze_entities(text))
    },
    "calculate" : {
        "patterns": [
            r"посчитать (.+)",
            r"сколько будет (.+)",
            r"вычислить (.+)",
            r"(?:вычислить|посчитать)\s*([\d+\-*/ ]+)"
        ],
        "handler": lambda expr: calculate(expr)
    },
    "datetime" : {
        "patterns": [r"дата и время", r"точное время и дата", r"время и дата"],
        "handler": lambda: datetime.datetime.now().strftime("Сейчас %H:%M:%S, %d.%m.%Y")
    },
    "time" : {
        "patterns": [r"который час", r"текущее время", r"сколько времени", r"^время$", r"^час$"],
        "handler": lambda: datetime.datetime.now().strftime("Сейчас %H:%M:%S")
    },
    "date" : {
        "patterns": [r"какое сегодня число", r"скажи сегодняшнюю дату", r"текущая дата", r"^дата$", r"^число$"],
        "handler": lambda: datetime.datetime.now().strftime("Сегодня %d.%m.%Y")
    },
    "day" : {
        "patterns": [r"\bкакой день недели\b", r"\bдень недели сегодня\b", r"\bкакой сегодня день недели\b", r"\bдень недели\b"],
        "handler": lambda: datetime.datetime.now().strftime("Сегодня %A")
    },
    "joke" : {
        "patterns": [r"анекдот", r"пошути", r"шутка", r"расскажи шутку", r"расскажи анекдот"],
        "responses": [
            "Почему программисты так любят зиму? Потому что код не ломается, когда замерзает! 😂",
            "Как программист решает проблему? Он просто меняет все на 0 и проверяет, исправилось ли! 🤓",
            "Какой чай пьёт программист? Виртуальный. Он же всегда в интернете! 🍵",
            "Что сказал один программист другому? Ты что, совсем с ума сошел? Это же баг, а не фича! 🤪",
            "Почему программисты никогда не играют в карты? Потому что у них всегда срабатывает исключение! 🃏",
            "Как программисты открывают окна? С помощью alt+tab! 😎"
        ]
    },
    "name" : {
        "patterns": [r"как тебя зовут", r"твое имя", r"ты кто", r"кто ты"],
        "responses": ["Я бот-помощник!", "Меня зовут Ботти", "Я твой виртуальный помощник"]
    },
    "compliment": {
        "patterns": [r"молодец", r"умница", r"супер", r"класс", r"замечательно"],
        "responses": ["Спасибо! Ты тоже супер!", "Очень приятно!"]
    },
    "mood": {
        "patterns": [
            r"(?:как дело|как ты|как настроение|как жизнь|как сам|как поживать)",
            r"(?:как твое дело|как у тебя дело)"
        ],
        "responses": [
            "Всё чудесно! Спасибо за вопрос!",
            "Всё отлично! А у тебя как?",
            "Спасибо за вопрос! У меня все хорошо!",
            "Неплохо, а у тебя как?"
        ]
    },
    "thanks": {
        "patterns": [
            r"(?:спасибо|благодарю|мерси|благодарствую|от души|ты лучший)",
            r"(?:огромное|большое)[ ]*(?:спасибо|благодарю)"
        ],
        "responses": [
            "Всегда пожалуйста! 😊",
            "Рад помочь! Обращайся ещё!",
            "Не стоит благодарности! 😉"
        ]
    },
    "search": {
        "patterns": [r"поиск (.+)", r"найди (.+)"],
        "handler": lambda query: search_web(query)
    },
    "quote": {
        "patterns": [r"цитата", r"мудрость"],
        "responses": [
            "Мы — это то, что мы делаем постоянно. — Аристотель",
            "Лучший способ предсказать будущее — создать его. — Авраам Линкольн"
        ]
    },
    "advice": {
        "patterns": [r"совет", r"рекомендация"],
        "responses": [
            "Попробуйте сегодня что-то новое!",
            "Совет дня: пейте больше воды."
        ]
    },
    "unknown" : {
        "patterns": [r".*"],
        "responses": [
            "Ааа... Можешь уточнить?",
            "Я не совсем понял тебя. Попробуй сказать иначе.",
            lambda x: f"Вы сказали: {x}" if random.random() < 0.3 else "Не совсем понял, можете повторить?"
        ]
    }
}

# Перевод текста
def translate_text(text, dest_language="ru"):
    try:
        translated = translator.translate(text, dest=dest_language)
        return translated.text
    except Exception as e:
        return "Не удалось перевести(. Попробуй снова"

# Анализ тональности текста с помощью TextBlob
def analyze_tone_textblob(text):
    try:
        translated_text = translate_text(text, "en")
        blob = TextBlob(translated_text)
        polarity = blob.sentiment.polarity
        if polarity > 0:
            return random.choice([
                "Кажется, ты в хорошем настроении! ",
                "О, как здорово! 😊 ",
                "Рад видеть тебя в хорошем расположении духа! 🌟 "
            ])
        elif polarity < 0:
            return random.choice([
                "Мне жаль, что ты расстроен(а). 😔 ",
                "Кажется, ты расстроен(а). Я тут, если нужно. ",
                "Кто-то не в лучшем настроении... Надеюсь, я смогу тебе помочь! 💙 "
            ])
        else:
            return ""
    except Exception as e:
        return "Сложно сейчас определить твоё настроение. Но я здесь, если что. "

# Анализ сущностей с помощью spaCy
def analyze_entities(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "LOC" or ent.label_ == "GPE":
            return ent.text
    return text

# Вычисление выражений
def calculate(expression):
    try:
        expression = expression.replace(" ", "")
        if not re.fullmatch(r"[\d+\-*/.()]+", expression):
            return "Что-то записано неверно."
        result = eval(expression)
        return f"Результат: {result}"
    except ZeroDivisionError:
        return "Кажется, ты пытаешься делить на ноль! Я так не умею."
    except Exception:
        return "Что-то не получилось."

# Поиск в интернете
def search_web(query):
    url = f"https://www.google.com/search?q={query.replace(' ','+')}"
    webbrowser.open(url)
    return random.choice([
        f"Ищу в интернете: {query}",
        f"Запрос: {query} принят в обработку",
        f"Идет поиск: {query}"
    ])

# Получение погоды
def get_weather(city):
    url_w = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
    try:
        response = requests.get(url_w)
        if response.status_code == 200:
            data = response.json()
            temp = data["main"]["temp"]
            weather_desc = data["weather"][0]["description"]
            return f"В городе {city.title()} сейчас {weather_desc} при температуре {temp} C."
        else:
            return "Не удалось получить информацию о погоде."
    except Exception:
        return "Ошибка при запросе погоды."

# Основная логика ответа бота
def chatbot_response(text):
    original_text = text.lower().strip()
    tone_response = analyze_tone_textblob(text)
    lemmatized_text = lemmatize_text(text.lower().strip())

    for intent_name, intent_data in INTENTS.items():
        for pattern in intent_data["patterns"]:
            match = re.search(pattern, original_text, re.IGNORECASE) if intent_name in ["echo", "greeting", "day", "thanks", "translate"] else re.search(pattern, lemmatized_text, re.IGNORECASE)
            if match:
                if "handler" in intent_data:
                    groups = match.groups()
                    response = intent_data["handler"](groups[0]) if groups else intent_data["handler"]()
                else:
                    chosen = random.choice(intent_data["responses"])
                    response = chosen(text) if callable(chosen) else chosen
                    #response = random.choice(intent_data["responses"])

                return f"{tone_response}{response}" if tone_response else response
    chosen = random.choice(INTENTS['unknown']['responses'])
    return f"{tone_response}{chosen(text) if callable(chosen) else chosen}" if tone_response else chosen(text) if callable(chosen) else chosen

# Основной цикл программы
if __name__ == "__main__":
    with open("chat_log.txt", "w", encoding="utf-8") as log_file:
        log_file.write("=" * 50 + "\n")

    print("Введите 'выход' для завершения диалога.")
    while True:
        user_input = input("Вы: ")
        if user_input.lower() == "выход" or user_input.lower() == "пока" or user_input.lower() == "до свидания":
            farewell = random.choice(INTENTS["goodbye"]["responses"])
            print("Бот:", farewell)
            log_interaction(user_input, farewell)
            break

        bot_reply = chatbot_response(user_input)
        print("Бот:", bot_reply)
        log_interaction(user_input, bot_reply)