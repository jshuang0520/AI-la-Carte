import sys
import os

# Insert the project root into sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config.config_parser import ConfigParser

def prompt_user(questions: dict, valid_options: dict) -> dict:
    """
    Prompt the user for each question.
    For questions with valid_options, display numbered choices.
    If the user's input contains a comma, process it as multiple selections.
    Otherwise, treat it as a single selection.
    """
    responses = {}
    for key, question in questions.items():
        options = valid_options.get(key)
        if options is not None and isinstance(options, list) and len(options) > 0:
            print("\n" + question)
            for idx, option in enumerate(options, 1):
                print(f"{idx}. {option}")
            while True:
                user_input = input("Enter your choice number (or for multiple selections, comma separated): ").strip()
                try:
                    if ',' in user_input:
                        # Process multiple selections
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
                        # Process single selection
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
            # If no valid options defined, accept free text.
            responses[key] = input(question).strip()
    return responses

def main():
    # Load configuration (config file is located at config/config.yaml)
    config = ConfigParser()
    print("Configuration loaded.\n")
    
    # Retrieve user preferences questions and valid options from the config.
    user_pref_questions = config.get("user_preferences.questions")
    user_pref_valid_options = config.get("user_preferences.valid_options", {})
    
    print("Please answer the following questions:")
    user_responses = prompt_user(user_pref_questions, user_pref_valid_options)
    
    print("\nUser Responses:")
    for key, answer in user_responses.items():
        print(f"{key}: {answer}")
    
    # Continue with further workflow logic using user_responses if needed.
    
if __name__ == "__main__":
    main()
