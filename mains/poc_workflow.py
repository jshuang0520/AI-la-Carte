import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from src.interface_helper import InterfaceHelper
from src.filter_helper import FilterHelper
from src.user_preferences.user_preferences import UserPreferences
from src.logger import Logger
from src.translate_helper import TranslateHelper
from src.rag_helper import RAGHelper
from typing import Dict, Any, List

class WorkflowInterface:
    """
    Main workflow interface that coordinates the recommendation process.
    Currently testing user data collection, translation, and prompt formation.
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
            
            # Step 3: Form RAG prompt
            self.logger.info("Forming RAG prompt...")
            prompt = self.rag_helper.create_prompt_template(translated_preferences)
            print(f"\nGenerated prompt: {prompt}")
            

            # Step 4: Get recommendations using filter helper
            recommended_stores = self.filter_helper.get_recommendations(
                user_preferences
            )
            print(f"\nRecommended stores:\n {recommended_stores}")
            
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
    """
    Main entry point for the application
    """
    try:
        workflow = WorkflowInterface()
        workflow.run_workflow()
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()

"""
TODO
1. add google docs questions
2. use miles for dist
3. copy geo_helper.py from Peeyush's branch
4. collect user info - backend input or worst case, frontend dropdown list


Would you like to get food today or another day this week? 
(Follow up: If another day, what day?)
Filter nearby sites by days of operation based on client preference. Interpret the week of the month field to know which distributions will be happening soonest.


What time of day would you like to pick up food?
Filter by hours of operation and see who is open on those hours of the day. 



output for further workflow:
Mar 24 Mon morning
Mar 24 Mon afternoon
Mar 25 Tue night
Mar 26 Wed evening

we need to pre-define the following time slot by our own: 
morning: 06:00 ~ 12:00, 
afternoon: 12:00 ~ 17:00, 
evening: 17:00 ~ 19:00, 
night: 19:00 ~ 00:00 
-> for SQL search and for customer's clarification
"""