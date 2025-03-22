from typing import Dict, Any, List
from src.logger import Logger
from src.geo_helper import GeoHelper
from src.rag_helper import RAGHelper
from src.translate_helper import TranslateHelper

class FilterHelper:
    def __init__(self):
        self.logger = Logger()
        self.geo_helper = GeoHelper()
        self.rag_helper = RAGHelper()
        self.translate_helper = TranslateHelper()
        
    def filter_stores(
        self,
        user_preferences: Dict[str, Any],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Main filtering function that coordinates between RAG and distance filtering
        """
        try:
            # Step 1: Get RAG-based recommendations
            rag_stores = self.rag_helper.perform_rag(
                self.rag_helper.create_prompt_template(user_preferences),
                top_n
            )
            
            # Step 2: Filter by distance
            user_location = self.geo_helper.parse_address(user_preferences['location'])
            max_distance = float(user_preferences['distance'])
            
            filtered_stores = self.geo_helper.filter_stores_by_distance(
                rag_stores,
                user_location,
                max_distance
            )
            
            # Step 3: Translate store details to user's preferred language
            translated_stores = []
            for store in filtered_stores:
                translated_store = self.translate_helper.translate_to_language(
                    store,
                    user_preferences['language']
                )
                translated_stores.append(translated_store)
            
            return translated_stores
        except Exception as e:
            self.logger.error(f"Error filtering stores: {str(e)}")
            raise
            
    def combine_results(
        self,
        rag_results: List[Dict[str, Any]],
        distance_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Combine results from RAG and distance filtering
        """
        try:
            # Create sets of store IDs for efficient lookup
            rag_store_ids = {store['id'] for store in rag_results}
            distance_store_ids = {store['id'] for store in distance_results}
            
            # Find stores that appear in both results
            common_store_ids = rag_store_ids.intersection(distance_store_ids)
            
            # Create dictionaries for quick lookup
            rag_dict = {store['id']: store for store in rag_results}
            distance_dict = {store['id']: store for store in distance_results}
            
            # Combine results
            combined_results = []
            for store_id in common_store_ids:
                store = rag_dict[store_id].copy()
                store['distance'] = distance_dict[store_id]['distance']
                combined_results.append(store)
            
            # Sort by distance
            return sorted(combined_results, key=lambda x: x['distance'])
        except Exception as e:
            self.logger.error(f"Error combining results: {str(e)}")
            raise 