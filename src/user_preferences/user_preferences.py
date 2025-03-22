from typing import Dict, Any, List
from src.logger import Logger
from src.translate_helper import TranslateHelper

class UserPreferences:
    def __init__(self):
        self.logger = Logger()
        self.translate_helper = TranslateHelper()
        self.questions = {
            'language': "Which language would you prefer to use? (en/es): ",
            'food_requirements': "What are your food requirements? (e.g., halal, kosher, vegetarian): ",
            'distance': "What is the maximum distance you can travel to get food? (in km): ",
            'time_slots': "What time slots are you available? (e.g., morning, afternoon, evening): ",
            'location': "Please enter your full address (country, city, street, zip code): "
        }
        
    def collect_preferences(self) -> Dict[str, Any]:
        """
        Collect user preferences through a series of questions
        """
        try:
            preferences = {}
            for key, question in self.questions.items():
                while True:
                    answer = input(question)
                    if self._validate_answer(key, answer):
                        preferences[key] = answer
                        break
                    print("Invalid input. Please try again.")
            return preferences
        except Exception as e:
            self.logger.error(f"Error collecting preferences: {str(e)}")
            raise
            
    def _validate_answer(self, key: str, answer: str) -> bool:
        """
        Validate user answers based on the question type
        """
        try:
            if key == 'language':
                return answer.lower() in ['en', 'es']
            elif key == 'distance':
                try:
                    float(answer)
                    return True
                except ValueError:
                    return False
            elif key == 'time_slots':
                valid_slots = ['morning', 'afternoon', 'evening']
                return all(slot.lower() in valid_slots for slot in answer.split(','))
            else:
                return bool(answer.strip())
        except Exception as e:
            self.logger.error(f"Error validating answer: {str(e)}")
            return False
            
    def verify_input(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Double check and correct user input for potential issues
        """
        try:
            verified = {}
            for key, value in preferences.items():
                if key == 'location':
                    # TODO: Implement address verification
                    verified[key] = value
                elif key == 'food_requirements':
                    # TODO: Implement food requirements verification
                    verified[key] = value
                else:
                    verified[key] = value
            return verified
        except Exception as e:
            self.logger.error(f"Error verifying input: {str(e)}")
            raise 