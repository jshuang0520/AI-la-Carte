import os
import yaml
from typing import Dict, Any, List, Optional
from src.logger import Logger

class Config:
    def __init__(self):
        self.logger = Logger()
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     'config', 'app_config.yaml')
            if not os.path.exists(config_path):
                self.logger.warning(f"Configuration file not found at {config_path}")
                return self._get_default_config()
                
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'environment': 'development',
            'db': {'path': 'data/database.db'},
            'languages': {
                'supported': ['en', 'es'],
                'default': 'en'
            },
            'distance': {
                'max_threshold': 10.0,
                'min_value': 0.0,
                'unit': 'mile'
            },
            'time': {
                'periods': ['morning', 'afternoon', 'evening', 'night'],
                'period_ranges': {
                    'morning': {'start': '06:00', 'end': '11:59'},
                    'afternoon': {'start': '12:00', 'end': '16:59'},
                    'evening': {'start': '17:00', 'end': '20:59'},
                    'night': {'start': '21:00', 'end': '23:59'}
                },
                'days_ahead': 7,
                'format': {
                    'date': '%b %d',
                    'time': '%H:%M'
                }
            },
            'log_level': 'INFO'
        }
        
    def get_nested(self, *keys: str, default: Any = None) -> Any:
        """Safely get nested configuration values"""
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
        return self.get_nested('environment', default='development')
        
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
        
    def get_distance_config(self) -> Dict[str, Any]:
        """Get distance configuration"""
        return self.get_nested('distance', default={
            'max_threshold': 10.0,
            'min_value': 0.0,
            'unit': 'mile'
        }) 