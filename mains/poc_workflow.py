import sys
import os
import logging

# Configure logging as needed
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Insert the project root into sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Updated imports from utilities
from src.utilities import load_config
from src.user_preferences.user_preferences import get_user_preferences
from src.geo_helper.geo_helper import GeoHelper
from src.translate_helper import TranslateHelper
from src.rag_helper.langchain import LangChainRAGHelper


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def filter_by_distance(user_prefs):
    max_distance = user_prefs.get('max_distance')
    logger.info("Filtering by distance using max_distance: %s", max_distance)
    geo_helper = GeoHelper()
    user_prefs['geo_data'] = geo_helper.find_nearby_food_assistance(
        user_prefs["keys"]["address"], 
        radius_miles=max(max_distance, user_prefs["distance"]["max_threshold"])
    )
    return user_prefs

# def filter_by_conditions(user_prefs):
#     logger.info("Filtering by additional conditions based on user preferences.")
#     return user_prefs

def rag_search(user_prefs, config):
    logger.info("Performing RAG search/comparison with user preferences...")
    logger.info("Running inference...")
    inference = LangChainRAGHelper(
        config["llm_config"]["LangChainRAGHelper"]["openai_api_key"]
    )
    raw_reference = inference.run_inference(user_prefs)
    logger.info(f"\n Raw reference: {raw_reference}")
    return {"result": {raw_reference}}

def main():
    try:
        # preparation
        config = load_config()
        translate_helper = TranslateHelper()
        # workflow
        user_prefs = get_user_preferences()
        filtered_prefs = filter_by_distance(user_prefs)
        # filtered_prefs = filter_by_conditions(filtered_prefs)
        results = rag_search(filtered_prefs, config=config)
        # FIXME: translate the results into the specified language
        translated_results = translate_helper.translate(
            from_lang="en", 
            to_lang=user_prefs['language'], 
            content=results
        )
        logger.info("Final Results: %s", results)
    except Exception as e:
        logger.error(f"Workflow error: {str(e)}")
        raise
    return results
    
if __name__ == "__main__":
    main()
