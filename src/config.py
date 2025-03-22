import os
from typing import Dict, Any
from src.logger import Logger

class Config:
    def __init__(self):
        self.logger = Logger()
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file
        """
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            return self._get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration
        """
        return {
            'db_path': 'data/database.db',
            'supported_languages': ['en', 'es'],
            'default_language': 'en',
            'max_distance_threshold': 1.0,
            'log_level': 'INFO'
        }
        
    def get_db_path(self) -> str:
        """
        Get database path
        """
        return self.config.get('db_path', 'data/database.db')
        
    def get_supported_languages(self) -> list:
        """
        Get supported languages
        """
        return self.config.get('supported_languages', ['en', 'es'])
        
    def get_default_language(self) -> str:
        """
        Get default language
        """
        return self.config.get('default_language', 'en')
        
    def get_max_distance_threshold(self) -> float:
        """
        Get maximum distance threshold
        """
        return self.config.get('max_distance_threshold', 1.0)
        
    def get_log_level(self) -> str:
        """
        Get log level
        """
        return self.config.get('log_level', 'INFO') 