import sys
import os
from datetime import datetime, timedelta

# Insert the project root into sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import load_config  # using our simple YAML loader

def get_available_time_slots(config):
    """
    Generate available time slots for the next 'days_ahead' days.
    Returns a list of strings like "Apr 04 morning", "Apr 04 afternoon", etc.
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

def get_time_slots_for_day(config, day_choice: str):
    """
    Generate available time slots for a specific day based on the user's choice.
    day_choice should be "today" or "tomorrow".
    """
    periods = config['time']['periods']
    date_format = config['time']['format']['date']
    now = datetime.now()
    if day_choice == "today":
        target_day = now
    elif day_choice == "tomorrow":
        target_day = now + timedelta(days=1)
    else:
        # If not today/tomorrow, fallback to full week.
        return get_available_time_slots(config)
    
    day_str = target_day.strftime(date_format)
    return [f"{day_str} {period}" for period in periods]

def prompt_user(questions: dict, valid_options: dict, config: dict) -> dict:
    """
    Prompt the user for each question.
    For questions with valid options, display numbered choices.
    If the key is 'pickup_time', dynamically generate time slots based on the user's
    answer to 'pickup_day' (if available).
    For multi-select questions, allow comma-separated numbers.
    """
    responses = {}
    for key, question in questions.items():
        if key == "pickup_time":
            # If the user has already answered 'pickup_day', use it to restrict time slots.
            pickup_day_answer = responses.get("pickup_day", None)
            if pickup_day_answer in ("today", "tomorrow"):
                options = get_time_slots_for_day(config, pickup_day_answer)
            else:
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
    
    # Retrieve user preferences questions and valid options from the config.
    user_pref_questions = config['user_preferences']['questions']
    user_pref_valid_options = config['user_preferences']['valid_options']
    
    print("Please answer the following questions:")
    responses = prompt_user(user_pref_questions, user_pref_valid_options, config)
    
    print("\nUser Responses:")
    for key, value in responses.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
