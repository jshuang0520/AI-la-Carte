import os
from typing import Dict, Any, List
from src.logger import Logger
from src.translate_helper import TranslateHelper
from src.config import Config

class UserPreferences:
    def __init__(self):
        self.logger = Logger()
        self.translate_helper = TranslateHelper()
        self.config = Config()
        self.questions = self.config.get_nested('user_preferences', 'questions', default={})
        self.keys = self.config.preference_keys
        
    def collect_preferences(self) -> Dict[str, Any]:
        """
        Collect user preferences, using config if in development mode
        """
        try:
            # If in development mode, use default values from config
            if self.config.is_development():
                self.logger.info("Using development configuration for user preferences")
                return self.config.get_nested('user_preferences', 'defaults', default={})
            
            # Otherwise, collect preferences interactively
            preferences = {}
            
            # Language preference
            preferences[self.keys.language] = input(self.questions.get('language', "Which language would you prefer to use? (en/es): "))
            
            # Food requirements
            preferences[self.keys.food_requirements] = input(self.questions.get('food_requirements', "What are your food requirements? (e.g., halal, kosher, vegetarian): "))
            
            # Maximum distance
            preferences[self.keys.max_distance] = float(input(self.questions.get('distance', "What is the maximum distance you can travel to get food? (in km): ")))
            
            # Time slots
            preferences[self.keys.time_slots] = input(self.questions.get('time_slots', "What time slots are you available? (e.g., morning, afternoon, evening): "))
            
            # Address
            preferences[self.keys.address] = input(self.questions.get('location', "Please enter your full address (country, city, street, zip code): "))
            
            return preferences
            
        except Exception as e:
            self.logger.error(f"Error collecting user preferences: {str(e)}")
            raise
            
    def _validate_answer(self, key: str, answer: str) -> bool:
        """
        Validate user answers based on the question type
        """
        try:
            if key == self.keys.language:
                valid_options = self.config.get_validation_options('language')
                return answer.lower() in valid_options
            elif key == self.keys.max_distance:
                try:
                    distance = float(answer)
                    distance_config = self.config.get_distance_config()
                    return distance >= distance_config['min_value']
                except ValueError:
                    return False
            elif key == self.keys.time_slots:
                valid_options = self.config.get_validation_options('time_slots')
                return all(slot.lower() in valid_options for slot in answer.split(','))
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
            valid_languages = self.config.get_validation_options('language')
            if preferences[self.keys.language] not in valid_languages:
                raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
                
            # Verify max distance is positive and within limits
            distance_config = self.config.get_distance_config()
            if preferences[self.keys.max_distance] <= distance_config['min_value']:
                raise ValueError(f"Maximum distance must be greater than {distance_config['min_value']} {distance_config['unit']}")
                
            # Verify time slots
            valid_slots = self.config.get_validation_options('time_slots')
            if not all(slot in valid_slots for slot in preferences[self.keys.time_slots].split(',')):
                raise ValueError(f"Time slots must be one of: {', '.join(valid_slots)}")
            
            return preferences
        except Exception as e:
            self.logger.error(f"Error verifying user preferences: {str(e)}")
            raise 