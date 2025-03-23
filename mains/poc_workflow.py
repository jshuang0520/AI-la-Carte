import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.interface_helper import InterfaceHelper
from src.filter_helper import FilterHelper
from src.user_preferences.user_preferences import UserPreferences
from src.logger import Logger
from typing import Dict, Any, List

class WorkflowInterface:
    """
    Main workflow interface that coordinates the recommendation process.
    All specific functionalities are delegated to appropriate helper classes.
    """
    def __init__(self):
        self.interface_helper = InterfaceHelper()
        self.filter_helper = FilterHelper()
        self.user_preferences = UserPreferences()
        self.logger = Logger()

    def run_workflow(self):
        """
        Main workflow execution that coordinates the entire recommendation process
        """
        try:
            # Step 1: Collect and validate user preferences
            user_preferences = self.user_preferences.collect_preferences()
            
            # Step 2: Get recommendations using filter helper
            # This internally coordinates RAG, geo filtering, and translations
            recommended_stores = self.filter_helper.get_recommendations(
                user_preferences
            )
            
            # Step 3: Display results in user's preferred language
            self.interface_helper.display_results(
                recommended_stores,
                user_preferences['language']
            )
            
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
