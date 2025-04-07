"""
Configuration package for the application.
Contains user preferences and other configuration settings.
"""

# from .config_parser import ConfigParser

# __all__ = ['ConfigParser'] 


from .config_parser import load_config
from .logger import Logger  # or whatever names you use
from .utils import *        # if you want to export all utility functions
