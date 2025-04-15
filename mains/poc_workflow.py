import sys
import os
import logging
import json

# Configure logging as needed
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Updated imports from utilities
from src.utilities.config_parser import load_config
from src.user_preferences.user_preferences import get_user_preferences
from src.geo_helper.geo_helper import GeoHelper
import src.rag_helper.langchain as lc


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def filter_by_distance(
        user_prefs, 
        config,
        limit=100
    ):
    max_distance = float(user_prefs.get('max_distance'))
    logger.info("Filtering by distance using max_distance: %s", max_distance)
    geo_helper = GeoHelper()
    distance_data = geo_helper.find_nearby_food_assistance(
        user_prefs["address"], 
        radius_miles=max(max_distance, config["distance"]["max_threshold"]),
        limit=limit
    )
    logger.info(
        "First three rows of distance data retrieved: %s", 
        distance_data[:3]
    )
    return distance_data


def rag_search(user_prefs, distance_data, config):
    logger.info("Performing RAG search/comparison with user preferences...")
    logger.info("Running inference...")
    INPUT_INFO = {"USER_PREFS": user_prefs, "Arcgis": distance_data}
    rag_system = lc.FoodAssistanceRAG(
        openai_api_key="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",
        db_path="/Users/johnson.huang/py_ds/AI-la-Carte/data/cafb.db",
        dietary_model="gpt-4o-mini",
        response_model="gpt-4o-mini"
    )
    response = rag_system.process_request(INPUT_INFO)
    return response

def main():
    try:
        # preparation
        config = load_config()
        # workflow
        user_prefs = get_user_preferences()
        distance_data = filter_by_distance(
            user_prefs, 
            config=config,
            limit=100,
        )
        results = rag_search(user_prefs, distance_data, config=config)
        logger.info("Final Results: %s", results)
    except Exception as e:
        logger.error(f"Workflow error: {str(e)}")
        raise
    return results
    
if __name__ == "__main__":
    main()
