import sys
import os

# Insert the project root into sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from src.interface_helper import InterfaceHelper
from src.filter_helper import FilterHelper
from src.user_preferences.user_preferences import UserPreferences
from src.logger import Logger
from src.translate_helper import TranslateHelper
from src.rag_helper import RAGHelper
from src.rag_helper.langchain import LangChainRAGHelper
from typing import Dict, Any, List

# Config.
config = {
    "LangChainRAGHelper": {
        "openai_api_key": "",
        "model_name": "gpt-4o-mini",
        "persist_directory": "chroma_data",
        "temperature": 0.0,
    },
}

class WorkflowInterface:
    """
    Prompt the user for each question.
    For questions with valid_options, display numbered choices.
    If the user's input contains a comma, process it as multiple selections.
    Otherwise, treat it as a single selection.
    """

    def __init__(self):
        self.interface_helper = InterfaceHelper()
        self.user_preferences = UserPreferences()
        self.translate_helper = TranslateHelper()
        self.filter_helper = FilterHelper() 
        self.rag_helper = RAGHelper()
        self.logger = Logger()

    def run_workflow(self):
        """
        Test workflow for user data collection and prompt formation
        """
        try:
            # Step 1: Collect and validate user preferences
            self.logger.info("Collecting user preferences...")
            user_preferences = self.user_preferences.collect_preferences()
            print(f"\nCollected preferences: {user_preferences}")
            
            # Step 2: Translate preferences if needed
            self.logger.info("Translating preferences...")
            translated_preferences = self.translate_helper.translate_to_english(user_preferences)
            print(f"\nTranslated preferences: {translated_preferences}")
            
            # Step 3: Run inference.
            self.logger.info("Running infernce")
            inference= LangChainRAGHelper(**config["LangChainRAGHelper"])
            raw_reference = inference.run_inference(user_preferences)
            print(f"\n Raw reference: {raw_reference}")
            
            # The following steps are commented out for now as we're testing only the first half
            """            
            # Step 5: Display results in user's preferred language
            self.interface_helper.display_results(
                recommended_stores,
                user_preferences['language']
            )
            """
            
        except Exception as e:
            self.logger.error(f"Workflow error: {str(e)}")
            raise


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