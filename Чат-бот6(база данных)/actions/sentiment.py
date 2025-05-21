from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from textblob import TextBlob
from googletrans import Translator

translator = Translator()

class ActionAnalyzeSentiment(Action):
    """Анализ тональности сообщения с расширенной логикой"""

    def name(self) -> Text:
        return "action_analyze_sentiment"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = tracker.latest_message.get('text')

        if not text or len(text.strip()) < 3:
            dispatcher.utter_message(text="Извините, не совсем понял вас. Можете уточнить?")
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