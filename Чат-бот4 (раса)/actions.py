from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from datetime import datetime
from textblob import TextBlob
import requests
import re
import logging
import math
from googletrans import Translator
import webbrowser
import urllib.parse

# Инициализация переводчика
translator = Translator()

class ActionTranslate(Action):
    """Перевод текста на английский"""

    def name(self) -> Text:
        return "action_translate"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text_to_translate = tracker.get_slot("text")

        if not text_to_translate:
            dispatcher.utter_message(text="Не нашёл текст для перевода. Попробуйте снова.")
            return []

        try:
            result = translator.translate(text_to_translate, dest='en').text
            msg = f"Перевод: {result}"
        except Exception as e:
            msg = "Не удалось выполнить перевод"

        dispatcher.utter_message(text=msg)
        return []


class ActionCalculate(Action):
    """Вычисление математических выражений"""

    def name(self) -> Text:
        return "action_calculate"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        expression = tracker.get_slot("expression")
        expression = expression.replace(" ", "").lower()

        # Замена русских символов
        expression = expression.replace('х', 'x').replace('÷', '/')

        # Проверка безопасности
        if not re.match(r'^[\d+\-*/().,x^]+$', expression):
            dispatcher.utter_message(text="Недопустимые символы в выражении")
            return []

        try:
            # Замена ^ на ** для Python
            expression = expression.replace('^', '**')
            result = eval(expression)
            msg = f"Результат: {round(result, 3)}"
        except ZeroDivisionError:
            msg = "Ошибка: деление на ноль"
        except Exception as e:
            msg = "Не могу вычислить это выражение"

        dispatcher.utter_message(text=msg)
        return []

class ActionDatetime(Action):
    """Получение текущей даты и времени"""

    def name(self) -> Text:
        return "action_datetime"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        now = datetime.now()
        response = now.strftime("Сейчас %H:%M:%S, %d.%m.%Y")
        dispatcher.utter_message(text=response)
        return []


class ActionSearch(Action):
    """Поиск в интернете"""

    def name(self) -> Text:
        return "action_search"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        query = tracker.get_slot("query")
        webbrowser.open(f"https://www.google.com/search?q={query}")
        dispatcher.utter_message(text=f"Ищу: {query}")
        return []

class ActionAnalyzeSentiment(Action):
    """Анализ тональности сообщения с расширенной логикой"""

    def name(self) -> Text:
        return "action_analyze_sentiment"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = tracker.latest_message.get('text')

        if not text or len(text.strip()) < 3:
            dispatcher.utter_message(text="Ваше сообщение слишком короткое для анализа")
            return []

        try:
            # Переводим текст на английский для более точного анализа
            translated = translator.translate(text, dest='en').text
            analysis = TextBlob(translated)

            # Определяем тон и субъективность
            polarity = analysis.sentiment.polarity  # -1 to 1 (negative to positive)
            subjectivity = analysis.sentiment.subjectivity  # 0 to 1 (objective to subjective)

            # Формируем ответ в зависимости от настроения
            if polarity > 0.3:
                if subjectivity > 0.6:
                    msg = "Вы выглядите очень счастливым! 😊 Что вас так радует?"
                else:
                    msg = "Чувствуется позитивный настрой! 👍"
            elif polarity < -0.3:
                if subjectivity > 0.6:
                    msg = "Кажется, вы расстроены. Хотите поговорить об этом? 💙"
                else:
                    msg = "Чувствуется негативный тон. Могу я чем-то помочь? 🤗"
            else:
                if subjectivity > 0.6:
                    msg = "Вы выглядите спокойным. Как ваши дела? 😌"
                else:
                    msg = "Спасибо за ваше сообщение! Как я могу вам помочь?"

            # Добавляем анализ эмоций
            dispatcher.utter_message(text=msg)

            # Сохраняем слот с настроением для персонализации
            mood = "positive" if polarity > 0.3 else ("negative" if polarity < -0.3 else "neutral")
            return [SlotSet("user_mood", mood)]

        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            dispatcher.utter_message(text="Я вас внимательно слушаю!")
            return []

class WeatherService:
    API_KEY = "f62350d6ff8c087ec53d1479dab00ade"

    @staticmethod
    def normalize_city_name(city: str) -> str:
        """
        Нормализует название города, удаляя предлоги и приводя к именительному падежу
        Примеры:
        - "в Москве" -> "Москва"
        - "для Санкт-Петербурга" -> "Санкт-Петербург"
        - "по Ростову-на-Дону" -> "Ростов-на-Дону"
        """
        # Удаляем предлоги и лишние пробелы
        city = re.sub(r'^[вдляпо]\s+', '', city.strip(), flags=re.IGNORECASE)

        # Приводим к нижнему регистру
        city = city.lower()

        # Обрабатываем составные названия (через дефис)
        if '-' in city:
            parts = city.split('-')
            city = '-'.join([WeatherService.normalize_part(part) for part in parts])
        else:
            city = WeatherService.normalize_part(city)

        return city.capitalize()

    @staticmethod
    def normalize_part(part: str) -> str:
        """Нормализует часть названия города"""
        # Удаляем окончания, характерные для русских падежей
        endings = [
            (r'ом$', ''),  # "ом" -> ""
            (r'е$', 'а'),  # "е" -> "а"
            (r'и$', 'ь'),  # "и" -> "ь"
            (r'у$', ''),  # "у" -> ""
            (r'ой$', 'а'),  # "ой" -> "а"
            (r'ом$', ''),  # "ом" -> ""
            (r'ы$', 'а'),  # "ы" -> "а"
            (r'ах$', 'а'),  # "ах" -> "а"
            (r'ям$', 'я'),  # "ям" -> "я"
            (r'городе$', 'город'),  # "городе" -> "город"
            (r'граде$', 'град'),  # "граде" -> "град"
            (r'ске$', 'ск'),  # "Новосибирске" -> "Новосибирск"
            (r'це$', 'к'),  # "Пензе" -> "Пенза" (обрабатывается предыдущим правилом)
            (r'ь$', 'ь')  # оставляем "ь" на конце
        ]

        for pattern, repl in endings:
            if re.search(pattern, part):
                part = re.sub(pattern, repl, part)
                break

        return part

    @classmethod
    def get_weather(cls, city: str) -> Dict[str, Any]:
        """Получает данные о погоде через API"""
        normalized_city = cls.normalize_city_name(city)
        encoded_city = urllib.parse.quote_plus(normalized_city)
        url = f"http://api.openweathermap.org/data/2.5/weather?q={encoded_city}&appid={cls.API_KEY}&units=metric&lang=ru"

        logger.info(f"Requesting weather for: {city} (normalized: {normalized_city})")
        response = requests.get(url, timeout=5)

        if response.status_code == 404:
            raise ValueError(f"Город '{normalized_city}' не найден")
        response.raise_for_status()

        return response.json()

logger = logging.getLogger(__name__)

class ActionWeather(Action):
    def name(self) -> Text:
        return "action_weather"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        try:
            # 1. Извлечение города
            city = next(
                (e["value"] for e in tracker.latest_message.get("entities", [])
                if e.get("entity") in ["city", "LOC"]),
                None
            )

            if not city:
                city = tracker.get_slot("city")

            if not city:
                dispatcher.utter_message(text="Укажите город, например: 'погода в Москве'")
                return []

            # 2. Запрос погоды
            data = WeatherService.get_weather(city)

            # 3. Формирование ответа
            response = (
                f"Погода в городе {data['name']}:\n"
                f"• {data['weather'][0]['description'].capitalize()}\n"
                f"• Температура: {data['main']['temp']:.1f}°C\n"
                f"• Ощущается как: {data['main']['feels_like']:.1f}°C\n"
                f"• Влажность: {data['main']['humidity']}%"
            )

            dispatcher.utter_message(text=response)
            return [SlotSet("city", data['name'])]

        except ValueError as e:
            dispatcher.utter_message(text=str(e))
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            dispatcher.utter_message(text="Ошибка при получении данных о погоде")

        return []