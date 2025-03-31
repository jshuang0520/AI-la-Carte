import os
import yaml
from typing import Dict, Any, List, Optional
from src.logger import Logger

class UserPreferencesConfig:
    def __init__(self, env: str = 'dev'):
        self.logger = Logger()
        self.config = self._load_config()
        self.env = env
        self._load_env_vars()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'user_preferences.yaml')
            if not os.path.exists(config_path):
                self.logger.error(f"Configuration file not found at {config_path}")
                return {}
                
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return {}
            
    def _load_env_vars(self):
        """Load environment variables for development mode"""
        try:
            if self.env == 'dev':
                env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'dev.env')
                if not os.path.exists(env_path):
                    self.logger.warning(f"Development environment file not found at {env_path}")
                    return
                    
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            try:
                                # Split on first occurrence of '=' only
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                
                                # Handle YAML-like arrays
                                if value.startswith('[') and value.endswith(']'):
                                    # Remove brackets and split by comma
                                    value = value[1:-1].strip()
                                    if value:
                                        # Split by comma and clean each item
                                        value = [item.strip().strip('"\'') for item in value.split(',')]
                                    else:
                                        value = []
                                else:
                                    # Remove quotes if present
                                    value = value.strip('"\'')
                                
                                # Update config with environment variable
                                self._update_config_with_env_var(key, value)
                                
                            except ValueError as e:
                                self.logger.warning(f"Invalid line in env file: {line}. Error: {str(e)}")
                                continue
                                
        except Exception as e:
            self.logger.error(f"Error loading environment variables: {str(e)}")
            
    def _update_config_with_env_var(self, key: str, value: Any):
        """Update config with environment variable value"""
        try:
            # Split key into parts (e.g., USER_PREFERENCES_KEYS_LANGUAGE -> ['user_preferences', 'keys', 'language'])
            parts = key.lower().split('_')
            
            # Remove 'user' and 'preferences' from the start
            if len(parts) >= 2 and parts[0] == 'user' and parts[1] == 'preferences':
                parts = parts[2:]
            
            # Navigate to the correct location in the config
            current = self.config
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the value
            current[parts[-1]] = value
            
        except Exception as e:
            self.logger.warning(f"Error updating config with env var {key}: {str(e)}")
            
    def get_key(self, category: str) -> str:
        """Get the key for a category"""
        return self.config.get('user_preferences', {}).get('keys', {}).get(category, category)
        
    def get_question(self, category: str) -> str:
        """Get the question for a category"""
        return self.config.get('user_preferences', {}).get('questions', {}).get(category, "")
        
    def get_valid_options(self, category: str) -> Optional[List[str]]:
        """Get valid options for a category"""
        return self.config.get('user_preferences', {}).get('valid_options', {}).get(category)
        
    def get_default_value(self, category: str) -> Optional[str]:
        """Get default value for a category"""
        return self.config.get('user_preferences', {}).get('defaults', {}).get(category)
        
    def get_category_config(self, category: str) -> Dict[str, Any]:
        """Get configuration for a specific category"""
        return self.config['user_preferences']['categories'].get(category, {}) 