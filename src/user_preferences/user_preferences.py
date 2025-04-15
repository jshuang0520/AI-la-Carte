import sys
import os
from datetime import datetime, timedelta

# # Insert the project root into sys.path.
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

from src.utilities import load_config  # from src/utilities/__init__.py

def get_available_time_slots(config):
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
    answers = []
    for q in follow_up_questions:
        answer = input(q).strip()
        answers.append(answer)
    return answers[0] if len(answers) == 1 else answers

def prompt_user(questions: dict, valid_options: dict, config: dict) -> dict:
    responses = {}
    follow_ups = {}
    # Load order and single_choice keys from config.
    order_keys = config['user_preferences'].get('order', {}).get('order', list(questions.keys()))
    single_choice_keys = config['user_preferences'].get('order', {}).get('single_choice', [])
    
    for key in order_keys:
        if key not in questions:
            continue
        question = questions[key]
        if key == "pickup_time":
            pickup_day_answer = responses.get("pickup_day", None)
            if pickup_day_answer in ("today", "tomorrow"):
                options = get_time_slots_for_day(config, pickup_day_answer)
            else:
                options = get_available_time_slots(config)
        else:
            options = valid_options.get(key)
        
        print("\n" + question)
        if options and isinstance(options, list) and len(options) > 0:
            display_options = [item.get("option") if isinstance(item, dict) else item for item in options]
            for idx, opt in enumerate(display_options, 1):
                print(f"{idx}. {opt}")
            
            while True:
                if key in single_choice_keys:
                    prompt_text = "Enter your choice number (single choice only): "
                else:
                    prompt_text = "Enter your choice number (or comma separated for multiple): "
                user_input = input(prompt_text).strip()
                # Enforce single choice if the key is in single_choice_keys.
                if key in single_choice_keys and ',' in user_input:
                    print("Please select only one option for this question.")
                    continue
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
            responses[key] = input().strip()
    if follow_ups:
        responses["follow_ups"] = follow_ups
    return responses

def get_user_preferences():
    # FIXME: (1)need to translate the follow-up questions and valid-options after an user specifies the language; (2) also, when collecting user's answer in the specified language, we should always trigger this function again to get the answer in English (as default)
    # TODO: question: shall we collect the responses in both languge (the specified language, and the default one in English)?
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
