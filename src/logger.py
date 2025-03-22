import logging
import os
from typing import Optional
from src.config import Config

class Logger:
    _instance: Optional['Logger'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
        
    def _initialize_logger(self):
        """
        Initialize logger
        """
        self.config = Config()
        self.logger = logging.getLogger('AI_la_Carte')
        self.logger.setLevel(self.config.get_log_level())
        
        # Create logs directory if it doesn't exist
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # File handler
        file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
        file_handler.setLevel(self.config.get_log_level())
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.config.get_log_level())
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def info(self, message: str):
        """
        Log info message
        """
        self.logger.info(message)
        
    def error(self, message: str):
        """
        Log error message
        """
        self.logger.error(message)
        
    def warning(self, message: str):
        """
        Log warning message
        """
        self.logger.warning(message)
        
    def debug(self, message: str):
        """
        Log debug message
        """
        self.logger.debug(message) 