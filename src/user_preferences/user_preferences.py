import os
import yaml
from typing import Dict, Any, List
from src.logger import Logger
from src.translate_helper import TranslateHelper

class UserPreferences:
    def __init__(self):
        self.logger = Logger()
        self.translate_helper = TranslateHelper()
        self.dev_config = self._load_dev_config()
        self.questions = {
            'language': "Which language would you prefer to use? (en/es): ",
            'food_requirements': "What are your food requirements? (e.g., halal, kosher, vegetarian): ",
            'distance': "What is the maximum distance you can travel to get food? (in km): ",
            'date': "What date would you like to receive the food? (YYYY-MM-DD): ",
            'time_slots': "What time slots are you available? (e.g., morning, afternoon, evening, night): ",
            'location': "Please enter your full address (country, city, street, zip code): "
        }
        
    def _load_dev_config(self) -> Dict[str, Any]:
        """
        Load development configuration if available
        """
        try:
            config_path = os.path.join('config', 'dev_config.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            return None
        except Exception as e:
            self.logger.warning(f"Could not load dev config: {str(e)}")
            return None
            
    def collect_preferences(self) -> Dict[str, Any]:
        """
        Collect user preferences, using dev config if available
        """
        try:
            # If in development mode and config exists, use default values
            if self.dev_config and self.dev_config.get('environment') == 'development':
                self.logger.info("Using development configuration for user preferences")
                return self.dev_config['user_preferences']
            
            # Otherwise, collect preferences interactively
            preferences = {}
            
            # Language preference
            preferences['language'] = input("Which language would you prefer to use? (en/es): ")
            
            # Food requirements
            preferences['food_requirements'] = input("What are your food requirements? (e.g., halal, kosher, vegetarian): ")

            # Maximum distance
            preferences['max_distance'] = float(input("What is the maximum distance you can travel to get food? (in km): "))

            # Date
            # preferences['date'] = input("What date would you like to receive the food? (YYYY-MM-DD): ")
            
            # Time slots
            preferences['time_slots'] = input("What time slots are you available? (e.g., morning, afternoon, evening): ")
            
            # Address
            preferences['address'] = input("Please enter your full address (country, city, street, zip code): ")
            
            # preferences['language'] = 'en'
            # preferences['food_requirements'] = 'vegeterian'
            # preferences['max_distance'] = 10.0
            # preferences['date'] = '2025-03-25'
            # preferences['time_slots'] = 'morning'
            # preferences['address'] = '3407 Tulane Dr, Hyattsville, MD, 20783'            
            return preferences
            
        except Exception as e:
            self.logger.error(f"Error collecting user preferences: {str(e)}")
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
        Verify user input meets requirements
        """
        try:
            # Verify language
            if preferences['language'] not in ['en', 'es']:
                raise ValueError("Language must be 'en' or 'es'")
                
            # Verify max distance is positive
            if preferences['max_distance'] <= 0:
                raise ValueError("Maximum distance must be positive")
                
            # Add more verifications as needed
            
            return preferences
        except Exception as e:
            self.logger.error(f"Error verifying user preferences: {str(e)}")
            raise 