from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests
import re
import logging
import urllib.parse
import pymorphy3

logger = logging.getLogger(__name__)
morph = pymorphy3.MorphAnalyzer()

class WeatherService:
    API_KEY = "f62350d6ff8c087ec53d1479dab00ade"

    @staticmethod
    def normalize_city_name(city: str) -> str:
        """Нормализация названия города, включая сложные формы и падежи"""
        city = re.sub(r'^\s*(в|во|из|на|по|для|о|об|от)\s+', '', city.strip(), flags=re.IGNORECASE)
        city_parts = re.split(r'[\s\-]+', city)

        normalized_parts = []
        for part in city_parts:
            parses = morph.parse(part)
            if parses:
                normal = parses[0].normal_form
                normalized_parts.append(normal.capitalize())
            else:
                normalized_parts.append(part.capitalize())

        return ' '.join(normalized_parts)

    @classmethod
    def get_weather(cls, city: str) -> Dict[str, Any]:
        """Получение данных о погоде"""
        normalized_city = cls.normalize_city_name(city)
        encoded_city = urllib.parse.quote_plus(normalized_city)
        url = f"http://api.openweathermap.org/data/2.5/weather?q={encoded_city}&appid={cls.API_KEY}&units=metric&lang=ru"

        response = requests.get(url, timeout=5)
        if response.status_code == 404:
            raise ValueError(f"Город '{normalized_city}' не найден")
        response.raise_for_status()
        return response.json()

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