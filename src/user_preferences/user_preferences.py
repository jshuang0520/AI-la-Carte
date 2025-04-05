import sys
import os
from datetime import datetime, timedelta

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
    If there’s exactly one question, return its answer as a string; else return a list.
    """
    answers = []
    for q in follow_up_questions:
        answer = input(q).strip()
        answers.append(answer)
    return answers[0] if len(answers) == 1 else answers

def prompt_user(questions: dict, valid_options: dict, config: dict) -> dict:
    """
    For each question in questions, display the question and its options (if defined) using print().
    Accept user input (allowing single or comma-separated numbers for multiple selections).
    If an option is defined as a dict with a "follow_up" field, prompt the corresponding follow-up questions.
    Returns a dictionary with the collected responses (including a "follow_ups" key if any).
    """
    responses = {}
    follow_ups = {}
    
    for key, question in questions.items():
        # For the special case of pickup_time, generate options based on the previously answered pickup_day.
        if key == "pickup_time":
            pickup_day_answer = responses.get("pickup_day", None)
            if pickup_day_answer in ("today", "tomorrow"):
                options = get_time_slots_for_day(config, pickup_day_answer)
            else:
                options = get_available_time_slots(config)
        else:
            options = valid_options.get(key)
        
        # Print the question once.
        print("\n" + question)
        if options and isinstance(options, list) and len(options) > 0:
            # Build display options (if option is a dict, use its 'option' field).
            display_options = [item.get("option") if isinstance(item, dict) else item for item in options]
            for idx, opt in enumerate(display_options, 1):
                print(f"{idx}. {opt}")
            
            while True:
                user_input = input("Enter your choice number (or comma separated for multiple): ").strip()
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
            # If there are no defined options, do not reprint the question; just call input().
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
