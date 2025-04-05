from typing import Any, Dict, List
import json
import os
from src.utilities.logger import Logger

class Utils:
    def __init__(self):
        self.logger = Logger()
        
    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """
        Load JSON file
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            Logger().error(f"Error loading JSON file: {str(e)}")
            raise
            
    @staticmethod
    def save_json(data: Dict[str, Any], file_path: str) -> bool:
        """
        Save data to JSON file
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            Logger().error(f"Error saving JSON file: {str(e)}")
            raise
            
    @staticmethod
    def ensure_dir(directory: str) -> None:
        """
        Ensure directory exists
        """
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except Exception as e:
            Logger().error(f"Error creating directory: {str(e)}")
            raise 