import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_parser import ConfigParser


def main():
    # Load the unified configuration from config.yaml
    config = ConfigParser("config.yaml")

    # Access various configuration values using dot notation
    environment = config.get("environment")
    db_path = config.get("db.path")
    log_level = config.get("log_level")
    
    # Example: Print application settings
    print("Application Environment:", environment)
    print("Database Path:", db_path)
    print("Log Level:", log_level)
    
    # Access language settings
    default_language = config.get("languages.default")
    supported_languages = config.get("languages.supported")
    print("Default Language:", default_language)
    print("Supported Languages:", supported_languages)
    
    # Access user preferences questions and defaults
    user_pref_keys = config.get("user_preferences.keys")
    user_pref_questions = config.get("user_preferences.questions")
    user_pref_defaults = config.get("user_preferences.defaults")
    
    print("\nUser Preferences Keys:")
    print(user_pref_keys)
    print("\nUser Preferences Questions:")
    for key, question in user_pref_questions.items():
        print(f"{key}: {question}")
    print("\nUser Preferences Defaults:")
    print(user_pref_defaults)
    
    # Here, you would implement the rest of your workflow logic.
    # For example, prompting the user with questions and processing responses.
    # (This is just a proof-of-concept to show how to access the configuration values.)

if __name__ == "__main__":
    main()
