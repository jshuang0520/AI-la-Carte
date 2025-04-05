import sys
import os
from datetime import datetime, timedelta

# Insert the project root into sys.path.
# File is at: AI-la-Carte/src/user_preferences/user_preferences.py,
# so project root is two levels up.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import load_config  # simple YAML loader

def get_available_time_slots(config):
    """
    Generate available time slots for the next 'days_ahead' days.
    Returns a list of strings like "Apr 04 morning", "Apr 04 afternoon", etc.
    """
    time_config = config.get('time', {})
    days_ahead = time_config.get('days_ahead', 7)
    periods = time_config.get('periods', ['morning', 'afternoon', 'evening', 'night'])
    date_format = time_config.get('format', {}).get('date', "%b %d")
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
    Generate available time slots for a specific day (today or tomorrow).
    """
    time_config = config.get('time', {})
    periods = time_config.get('periods', ['morning', 'afternoon', 'evening', 'night'])
    date_format = time_config.get('format', {}).get('date', "%b %d")
    now = datetime.now()
    if day_choice == "today":
        target_day = now
    elif day_choice == "tomorrow":
        target_day = now + timedelta(days=1)
    else:
        return get_available_time_slots(config)
    
    day_str = target_day.strftime(date_format)
    return [f"{day_str} {period}" for period in periods]

def prompt_follow_up(follow_up_questions: list):
    """
    Prompt the user with follow-up questions.
    If there's exactly one question, return the answer as a string.
    Otherwise, return a list of answers.
    """
    answers = []
    for q in follow_up_questions:
        answer = input(q).strip()
        answers.append(answer)
    return answers[0] if len(answers) == 1 else answers

def prompt_user(questions: dict, valid_options: dict, config: dict) -> dict:
    """
    Prompt the user for each question.
    For questions with valid options, display numbered choices.
    If the key is 'pickup_time', generate time slots based on the user's
    answer to 'pickup_day'.
    For multi-select questions, allow comma-separated numbers.
    If an option has follow-up questions, prompt for them and store their answers.
    The questions and options are shown using print(), while the final responses
    (including follow-ups) are collected into a dictionary.
    """
    responses = {}
    follow_ups = {}  # To collect follow-up responses.
    
    for key, question in questions.items():
        # Special handling for pickup_time based on pickup_day answer.
        if key == "pickup_time":
            pickup_day_answer = responses.get("pickup_day", None)
            if pickup_day_answer in ("today", "tomorrow"):
                options = get_time_slots_for_day(config, pickup_day_answer)
            else:
                options = get_available_time_slots(config)
        else:
            options = valid_options.get(key)
        
        # Show the question and its options using print.
        print("\n" + question)
        if options and isinstance(options, list) and len(options) > 0:
            # Prepare display options: if an option is a dict, display its 'option' field; otherwise, the string.
            display_options = []
            for item in options:
                if isinstance(item, dict):
                    display_options.append(item.get("option"))
                else:
                    display_options.append(item)
            for idx, option in enumerate(display_options, 1):
                print(f"{idx}. {option}")
            
            while True:
                user_input = input("Enter your choice number (or for multiple selections, comma separated): ").strip()
                try:
                    if ',' in user_input:
                        selections = [s.strip() for s in user_input.split(",") if s.strip()]
                        chosen = []
                        chosen_followups = {}
                        for s in selections:
                            if not s.isdigit():
                                raise ValueError("Each selection must be a number.")
                            idx_choice = int(s)
                            if idx_choice < 1 or idx_choice > len(display_options):
                                raise ValueError("Choice out of range.")
                            selected_item = options[idx_choice - 1]
                            if isinstance(selected_item, dict):
                                chosen.append(selected_item.get("option"))
                                if "follow_up" in selected_item:
                                    print(f"\nFollow-up for option '{selected_item.get('option')}':")
                                    follow_resp = prompt_follow_up(selected_item["follow_up"])
                                    chosen_followups[selected_item.get("option")] = follow_resp
                            else:
                                chosen.append(selected_item)
                        responses[key] = chosen
                        if chosen_followups:
                            follow_ups[key] = chosen_followups
                    else:
                        if not user_input.isdigit():
                            raise ValueError("Input must be a number.")
                        idx_choice = int(user_input)
                        if idx_choice < 1 or idx_choice > len(display_options):
                            raise ValueError("Choice out of range.")
                        selected_item = options[idx_choice - 1]
                        if isinstance(selected_item, dict):
                            responses[key] = selected_item.get("option")
                            if "follow_up" in selected_item:
                                print(f"\nFollow-up for option '{selected_item.get('option')}':")
                                follow_resp = prompt_follow_up(selected_item["follow_up"])
                                follow_ups[key] = {selected_item.get("option"): follow_resp}
                        else:
                            responses[key] = selected_item
                    break
                except ValueError as e:
                    print("Invalid input:", e, "Please try again.")
        else:
            # If no valid options defined, accept free text.
            responses[key] = input().strip()
    if follow_ups:
        responses["follow_ups"] = follow_ups
    return responses

def get_user_preferences():
    """
    Load the configuration, then prompt the user using the questions and valid options from the config.
    Returns the collected responses dictionary.
    """
    config = load_config()
    user_pref_questions = config['user_preferences']['questions']
    user_pref_valid_options = config['user_preferences']['valid_options']
    print("Please answer the following questions:")
    responses = prompt_user(user_pref_questions, user_pref_valid_options, config)
    return responses

if __name__ == "__main__":
    prefs = get_user_preferences()
    print("\nCollected Preferences:")
    print(prefs)
