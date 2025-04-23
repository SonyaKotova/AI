from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from datetime import datetime

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