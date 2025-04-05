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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def filter_by_distance(user_prefs):
    max_distance = user_prefs.get('max_distance')
    logger.info("Filtering by distance using max_distance: %s", max_distance)
    return user_prefs

def filter_by_conditions(user_prefs):
    logger.info("Filtering by additional conditions based on user preferences.")
    return user_prefs

def rag_search(user_prefs):
    logger.info("Performing RAG search/comparison with user preferences.")
    return {"result": "Sample result based on user preferences."}

def main():
    config = load_config()
    user_prefs = get_user_preferences()
    filtered_prefs = filter_by_distance(user_prefs)
    filtered_prefs = filter_by_conditions(filtered_prefs)
    results = rag_search(filtered_prefs)
    logger.info("Final Results: %s", results)
    return results

if __name__ == "__main__":
    main()
