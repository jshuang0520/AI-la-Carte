import os
import yaml
from typing import Dict, Any, List, Union
from src.logger import Logger

class PreferenceKeys:
    """
    Structured access to preference keys from configuration
    """
    def __init__(self, config: Dict[str, Any]):
        keys = config.get('user_preferences', {}).get('keys', {})
        self.language = keys.get('language', 'language')
        self.food_requirements = keys.get('food_requirements', 'food_requirements')
        self.max_distance = keys.get('max_distance', 'max_distance')
        self.time_slots = keys.get('time_slots', 'time_slots')
        self.address = keys.get('address', 'address')

class Config:
    def __init__(self):
        self.logger = Logger()
        self.config = self._load_config()
        self.preference_keys = PreferenceKeys(self.config)
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file
        """
        try:
            # Load main configuration
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'app_config.yaml')
            if not os.path.exists(config_path):
                self.logger.warning(f"Configuration file not found at {config_path}, using defaults")
                return self._get_default_config()
                
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Load environment-specific configuration if exists
            env = os.getenv('APP_ENV', 'production')
            env_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', f'{env}_config.yaml')
            if os.path.exists(env_config_path):
                with open(env_config_path, 'r') as f:
                    env_config = yaml.safe_load(f)
                    self._deep_update(config, env_config)
                    
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return self._get_default_config()
            
    def _deep_update(self, d: dict, u: dict) -> None:
        """
        Recursively update a dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
                
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration - this should match the structure of app_config.yaml
        """
        return {
            'environment': 'production',
            'db': {'path': 'data/database.db'},
            'languages': {
                'supported': ['en', 'es'],
                'default': 'en'
            },
            'distance': {
                'max_threshold': 1.0,
                'min_value': 0.0,
                'unit': 'km'
            },
            'log_level': 'INFO',
            'user_preferences': {
                'keys': {
                    'language': 'language',
                    'food_requirements': 'food_requirements',
                    'max_distance': 'max_distance',
                    'time_slots': 'time_slots',
                    'address': 'address'
                },
                'questions': {},
                'validation': {
                    'time_slots': {'valid_options': ['morning', 'afternoon', 'evening']},
                    'language': {'valid_options': ['en', 'es']}
                },
                'defaults': {
                    'language': 'en',
                    'food_requirements': '',
                    'max_distance': 5,
                    'time_slots': 'morning',
                    'address': ''
                }
            }
        }
        
    def get_nested(self, *keys: str, default: Any = None) -> Any:
        """
        Safely get nested configuration values
        """
        current = self.config
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key, default)
            if current is None:
                return default
        return current
        
    def get_environment(self) -> str:
        """Get current environment"""
        return self.get_nested('environment', default='production')
        
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.get_environment() == 'development'
        
    def get_db_path(self) -> str:
        """Get database path"""
        return self.get_nested('db', 'path', default='data/database.db')
        
    def get_supported_languages(self) -> List[str]:
        """Get supported languages"""
        return self.get_nested('languages', 'supported', default=['en', 'es'])
        
    def get_default_language(self) -> str:
        """Get default language"""
        return self.get_nested('languages', 'default', default='en')
        
    def get_distance_config(self) -> Dict[str, Union[float, str]]:
        """Get distance configuration"""
        return self.get_nested('distance', default={
            'max_threshold': 1.0,
            'min_value': 0.0,
            'unit': 'km'
        })
        
    def get_user_preferences_config(self) -> Dict[str, Any]:
        """Get user preferences configuration"""
        return self.get_nested('user_preferences', default={})
        
    def get_validation_options(self, field: str) -> List[str]:
        """Get validation options for a specific field"""
        return self.get_nested('user_preferences', 'validation', field, 'valid_options', default=[]) 