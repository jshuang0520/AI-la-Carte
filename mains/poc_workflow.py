import sys
import os
from datetime import datetime, timedelta

# Insert the project root into sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import load_config  # Import load_config from src/config/__init__.py

def get_available_time_slots(config):
    """
    Generate available time slots for the next 'days_ahead' days.
    Uses the periods and date format from the configuration.
    """
    days_ahead = config['time']['days_ahead']
    periods = config['time']['periods']
    date_format = config['time']['format']['date']
    now = datetime.now()
    slots = []
    for d in range(0, days_ahead + 1):
        day = now + timedelta(days=d)
        day_str = day.strftime(date_format)
        for period in periods:
            slots.append(f"{day_str} {period}")
    return slots

def prompt_user(questions: dict, valid_options: dict, config: dict) -> dict:
    """
    Prompt the user for each question.
    For questions with valid options, display numbered choices.
    If the key is 'pickup_time', dynamically generate time slots.
    For multi-select questions, allow comma-separated numbers.
    """
    responses = {}
    for key, question in questions.items():
        if key == "pickup_time":
            options = get_available_time_slots(config)
        else:
            options = valid_options.get(key)
        
        if options and isinstance(options, list) and len(options) > 0:
            print("\n" + question)
            for idx, option in enumerate(options, 1):
                print(f"{idx}. {option}")
            while True:
                user_input = input("Enter your choice number (or for multiple selections, comma separated): ").strip()
                try:
                    if ',' in user_input:
                        selections = [s.strip() for s in user_input.split(",") if s.strip()]
                        chosen = []
                        for s in selections:
                            if not s.isdigit():
                                raise ValueError("Each selection must be a number.")
                            idx_choice = int(s)
                            if idx_choice < 1 or idx_choice > len(options):
                                raise ValueError("Choice out of range.")
                            chosen.append(options[idx_choice - 1])
                        responses[key] = chosen
                    else:
                        if not user_input.isdigit():
                            raise ValueError("Input must be a number.")
                        idx_choice = int(user_input)
                        if idx_choice < 1 or idx_choice > len(options):
                            raise ValueError("Choice out of range.")
                        responses[key] = options[idx_choice - 1]
                    break
                except ValueError as e:
                    print("Invalid input:", e, "Please try again.")
        else:
            responses[key] = input(question).strip()
    return responses

def main():
    config = load_config()  # Loads config/config.yaml into a dictionary.
    print("Configuration loaded.\n")
    
    user_pref_questions = config['user_preferences']['questions']
    user_pref_valid_options = config['user_preferences']['valid_options']
    
    print("Please answer the following questions:")
    responses = prompt_user(user_pref_questions, user_pref_valid_options, config)
    
    print("\nUser Responses:")
    for key, value in responses.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
