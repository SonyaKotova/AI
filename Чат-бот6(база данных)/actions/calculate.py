from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import re

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