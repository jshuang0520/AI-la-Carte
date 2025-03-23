import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.embedding_helper import EmbeddingHelper
from src.db_helper import DBHelper
from src.translate_helper import TranslateHelper
from src.interface_helper import InterfaceHelper
from src.parser_helper import ParserHelper
from src.filter_helper import FilterHelper
from src.utils import Utils
from src.config import Config
from src.logger import Logger
from src.constants import Constants
from src.user_preferences.user_preferences import UserPreferences
from src.rag_helper.rag_helper import RAGHelper
from src.geo_helper.geo_helper import GeoHelper
from typing import Dict, Any, List


# translate data into all languages (En, Spanish)

# design db to store multi-language data


# collect user's customized information


# translate customized language to English, and show results in their customized language


# parse information


# filter according to
## non-math info
## math info (distance)
## combine the results (if needed)


# show the translated results


# create interface
# - try to write some pseudo code (annotation)

class WorkflowInterface:
    def __init__(self):
        self.embedding_helper = EmbeddingHelper()
        self.db_helper = DBHelper()
        self.translate_helper = TranslateHelper()
        self.interface_helper = InterfaceHelper()
        self.parser_helper = ParserHelper()
        self.filter_helper = FilterHelper()
        self.logger = Logger()
        self.config = Config()
        self.constants = Constants()
        self.user_preferences = UserPreferences()
        self.rag_helper = RAGHelper()
        self.geo_helper = GeoHelper()

    def translate_data(self, input_data):
        """
        Translate input data into multiple languages (English and Spanish)
        """
        try:
            # Translate to English
            en_data = self.translate_helper.translate_to_english(input_data)
            # Translate to Spanish
            es_data = self.translate_helper.translate_to_spanish(input_data)
            return {
                self.constants.LANG_EN: en_data,
                self.constants.LANG_ES: es_data
            }
        except Exception as e:
            self.logger.error(f"Translation error: {str(e)}")
            raise

    def store_multi_language_data(self, translated_data):
        """
        Store multi-language data in the database
        """
        try:
            # Store English version
            self.db_helper.store_data(translated_data[self.constants.LANG_EN], self.constants.LANG_EN)
            # Store Spanish version
            self.db_helper.store_data(translated_data[self.constants.LANG_ES], self.constants.LANG_ES)
            return True
        except Exception as e:
            self.logger.error(f"Database storage error: {str(e)}")
            raise

    def collect_user_preferences(self):
        """
        Collect and verify user preferences
        """
        try:
            # Collect preferences
            preferences = self.user_preferences.collect_preferences()
            
            # Verify input
            verified_preferences = self.user_preferences.verify_input(preferences)
            
            return verified_preferences
        except Exception as e:
            self.logger.error(f"Error collecting user preferences: {str(e)}")
            raise

    def process_user_input(self, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user preferences and prepare for store recommendations
        """
        try:
            # Create prompt template
            template = self.rag_helper.create_prompt_template(user_preferences)
            
            # Format prompt
            prompt = self.rag_helper.format_prompt(template, user_preferences)
            
            return {
                'prompt': prompt,
                'preferences': user_preferences
            }
        except Exception as e:
            self.logger.error(f"Error processing user input: {str(e)}")
            raise

    def get_store_recommendations(
        self, 
        processed_input: Dict[str, Any],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get store recommendations using both RAG and distance filtering
        """
        try:
            # Get RAG-based recommendations
            rag_stores = self.rag_helper.perform_rag(
                processed_input['prompt'],
                top_n
            )
            
            # Get user location and max distance
            user_location = self.geo_helper.parse_address(
                processed_input['preferences']['location']
            )
            max_distance = float(processed_input['preferences']['distance'])
            
            # Filter stores by distance
            filtered_stores = self.geo_helper.filter_stores_by_distance(
                rag_stores,
                user_location,
                max_distance
            )
            
            return filtered_stores
        except Exception as e:
            self.logger.error(f"Error getting store recommendations: {str(e)}")
            raise

    def display_results(
        self, 
        stores: List[Dict[str, Any]], 
        user_preferences: Dict[str, Any]
    ):
        """
        Display results in user's preferred language
        """
        try:
            # Format results
            formatted_results = self.interface_helper.format_results(stores)
            
            # Display in user's preferred language
            self.interface_helper.display(
                formatted_results,
                user_preferences['language']
            )
        except Exception as e:
            self.logger.error(f"Error displaying results: {str(e)}")
            raise

    def run_workflow(self):
        """
        Main workflow execution
        """
        try:
            # Step 1: Collect user preferences
            user_preferences = self.collect_user_preferences()
            
            # Step 2: Process user input
            processed_input = self.process_user_input(user_preferences)
            
            # Step 3: Get store recommendations
            recommended_stores = self.get_store_recommendations(processed_input)
            
            # Step 4: Display results
            self.display_results(recommended_stores, user_preferences)
            
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
