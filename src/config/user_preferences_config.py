import os
import yaml
import json
from typing import Dict, Any, List, Optional
from src.logger import Logger

class UserPreferencesConfig:
    def __init__(self, env: str = 'dev'):
        self.logger = Logger()
        self.env = env
        self.env_vars = self._load_env_vars()
        self.config = self._load_config()
        
    def _load_env_vars(self) -> Dict[str, Any]:
        """Load environment variables from .env file"""
        try:
            env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                  'config', f'{self.env}.env')
            if not os.path.exists(env_file):
                self.logger.warning(f"Environment file not found at {env_file}")
                return {}
                
            env_vars = {}
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Handle JSON arrays and null values
                        if value.startswith('[') and value.endswith(']'):
                            value = json.loads(value)
                        elif value.lower() == 'null':
                            value = None
                        elif value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]  # Remove quotes
                            
                        env_vars[key] = value
                        
            return env_vars
            
        except Exception as e:
            self.logger.error(f"Error loading environment variables: {str(e)}")
            return {}
            
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file and substitute environment variables"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     'config', 'user_preferences.yaml')
            if not os.path.exists(config_path):
                self.logger.warning(f"Configuration file not found at {config_path}")
                return self._get_default_config()
                
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Substitute environment variables
            self._substitute_env_vars(config)
            return config
                
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return self._get_default_config()
            
    def _substitute_env_vars(self, config: Dict[str, Any]) -> None:
        """Recursively substitute environment variables in the configuration"""
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, (dict, list)):
                    self._substitute_env_vars(value)
                elif isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_key = value[2:-1]  # Remove ${ and }
                    if env_key in self.env_vars:
                        config[key] = self.env_vars[env_key]
        elif isinstance(config, list):
            for i, value in enumerate(config):
                if isinstance(value, (dict, list)):
                    self._substitute_env_vars(value)
                elif isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_key = value[2:-1]  # Remove ${ and }
                    if env_key in self.env_vars:
                        config[i] = self.env_vars[env_key]
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'user_preferences': {
                'categories': {
                    'language': {
                        'key': 'language',
                        'question': 'Which language would you prefer to use? (en/es): ',
                        'valid_options': ['en', 'es'],
                        'default': 'en'
                    },
                    'food_requirements': {
                        'key': 'food_requirements',
                        'question': 'What are your food requirements? (e.g., halal, kosher, vegetarian): ',
                        'valid_options': ['halal', 'kosher', 'vegetarian', 'vegan', 'none'],
                        'default': 'none'
                    },
                    'max_distance': {
                        'key': 'max_distance',
                        'question': 'What is the maximum distance you can travel to get food? (in miles): ',
                        'valid_options': None,
                        'default': 10
                    },
                    'time_slots': {
                        'key': 'time_slots',
                        'question': 'What time slots are you available? (e.g., morning, afternoon, evening): ',
                        'valid_options': ['morning', 'afternoon', 'evening', 'night'],
                        'default': 'morning'
                    },
                    'address': {
                        'key': 'address',
                        'question': 'Please enter your full address (country, city, street, zip code): ',
                        'valid_options': None,
                        'default': '5702 Vassar Drive, College Park, Maryland, 20740'
                    },
                    'pickup_datetime': {
                        'key': 'pickup_datetime',
                        'question': 'When would you like to pick up food?',
                        'valid_options': None,
                        'default': ''
                    },
                    'services': {
                        'key': 'services',
                        'question': 'Which services do you need? (Select from the list): ',
                        'valid_options': ["Behavioral Healthcare", "Case management", "Childcare", "ESL", "Financial advising", "Financial assistance", "Gov't benefits enrollment", "Healthcare", "Housing", "Info on gov't benefits", "Job training/ workforce development", "Legal services", "Non-food items", "Nutrition Education Materials and Resources", "Programming/ support for older adults"],
                        'default': ''
                    }
                }
            }
        }
        
    def get_category_config(self, category: str) -> Dict[str, Any]:
        """Get configuration for a specific category"""
        return self.config['user_preferences']['categories'].get(category, {})
        
    def get_question(self, category: str) -> str:
        """Get question for a specific category"""
        return self.get_category_config(category).get('question', '')
        
    def get_valid_options(self, category: str) -> Optional[List[str]]:
        """Get valid options for a specific category"""
        return self.get_category_config(category).get('valid_options')
        
    def get_default_value(self, category: str) -> Any:
        """Get default value for a specific category"""
        return self.get_category_config(category).get('default')
        
    def get_key(self, category: str) -> str:
        """Get key for a specific category"""
        return self.get_category_config(category).get('key', '') 