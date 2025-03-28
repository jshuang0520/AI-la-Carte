"""
Configuration package for the application.
Contains user preferences and other configuration settings.
"""

from .base_config import Config
from .user_preferences_config import UserPreferencesConfig

__all__ = ['Config', 'UserPreferencesConfig'] 