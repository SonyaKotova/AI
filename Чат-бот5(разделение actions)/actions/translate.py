from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from googletrans import Translator

translator = Translator()


class ActionTranslate(Action):
    def name(self) -> Text:
        return "action_translate"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Получаем текст из entities
        text_to_translate = next(tracker.get_latest_entity_values("text"), None)

        # Если не нашли через entity, пробуем извлечь текст после "переведи"
        if not text_to_translate:
            message = tracker.latest_message.get('text', '')
            if 'переведи' in message.lower():
                text_to_translate = message.split('переведи')[-1].strip()
                # Удаляем возможные окончания типа "на английский"
                text_to_translate = text_to_translate.split('на ')[0].strip()

        if not text_to_translate:
            dispatcher.utter_message(text="Не нашёл текст для перевода. Попробуйте так: 'переведи слово кот'")
            return []

        try:
            result = translator.translate(text_to_translate, dest='en').text
            msg = f"Перевод: {result}"
        except Exception as e:
            msg = f"Не удалось выполнить перевод: {str(e)}"

        dispatcher.utter_message(text=msg)
        return []