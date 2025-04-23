from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import webbrowser


class ActionSearch(Action):
    def name(self) -> Text:
        return "action_search"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Получаем query из последнего сообщения
        query = next(tracker.get_latest_entity_values("query"), None)

        # Если не нашли через entity, пробуем извлечь текст после "найди"
        if not query:
            message = tracker.latest_message.get('text', '')
            if 'найди' in message.lower():
                query = message.split('найди')[-1].strip()
            elif 'поиск' in message.lower():
                query = message.split('поиск')[-1].strip()

        if not query:
            dispatcher.utter_message(text="Не удалось определить, что искать. Уточните запрос.")
            return []

        webbrowser.open(f"https://www.google.com/search?q={query}")
        dispatcher.utter_message(text=f"Ищу: {query}")
        return []