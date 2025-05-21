from rasa_sdk.events import SlotSet
from typing import Text, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from database import UserDatabase
import json
from datetime import datetime

class ActionSaveUserData(Action):
    def name(self):
        return "action_save_user_data"

    def run(self, dispatcher, tracker, domain):
        user_db = UserDatabase()
        user_data = {
            "user_id": tracker.sender_id,
            "username": tracker.get_slot("username"),
            "theme": tracker.get_slot("theme"),
            "language": tracker.get_slot("language"),
            "last_activity": datetime.now().isoformat(),
            "email": tracker.get_slot("email"),
            "city": tracker.get_slot("city"),
            "hobbies": json.dumps(tracker.get_slot("hobbies"))  # Для списков
        }
        user_db.save_user(user_data)
        user_db.close()
        #if tracker.get_slot("city"):
         #   dispatcher.utter_message(text=f"Город {tracker.get_slot('city')} сохранен! 🌆")
        #else:
         #   dispatcher.utter_message(text="Данные сохранены!")
        return []

class ActionLoadUserData(Action):
    def name(self) -> Text:
        return "action_load_user_data"
    def run(self, dispatcher, tracker, domain):
        user_db = UserDatabase()
        user_data = user_db.get_user(tracker.sender_id)  # Используется текущий sender_id
        user_db.close()

        if not user_data:
            return []

        # Обработка hobbies
        hobbies = user_data.get("hobbies")
        if hobbies:
            try:
                hobbies = json.loads(hobbies)
            except:
                hobbies = []
        else:
            hobbies = []

        return [
            SlotSet("username", user_data.get("username")),
            SlotSet("city", user_data.get("city")),
            SlotSet("hobbies", hobbies),
            SlotSet("theme", user_data.get("theme")),
            SlotSet("language", user_data.get("language")),
            SlotSet("email", user_data.get("email"))
        ]
