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
        
    def get_recommendations(
        self,
        user_preferences: Dict[str, Any],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Main recommendation function that coordinates RAG, geo filtering, and translations
        """
        try:
            # Step 1: Get RAG-based recommendations
            rag_stores = self.rag_helper.get_relevant_stores(
                user_preferences,
                top_n
            )
            
            # Step 2: Filter by distance
            filtered_stores = self.geo_helper.filter_by_distance(
                rag_stores,
                user_preferences['location'],
                float(user_preferences['distance'])
            )
            
            # Step 3: Translate results to user's preferred language
            translated_stores = self.translate_helper.translate_stores(
                filtered_stores,
                user_preferences['language']
            )
            
            # Step 4: Sort by relevance and distance
            return self._sort_results(translated_stores)
            
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {str(e)}")
            raise
            
    def _sort_results(
        self,
        stores: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Sort results by a combination of relevance score and distance
        """
        try:
            # Sort first by relevance score (if available)
            stores_with_score = sorted(
                stores,
                key=lambda x: x.get('relevance_score', 0),
                reverse=True
            )
            
            # Then sort by distance within same relevance groups
            return sorted(
                stores_with_score,
                key=lambda x: x.get('distance', float('inf'))
            )
            
        except Exception as e:
            self.logger.error(f"Error sorting results: {str(e)}")
            raise 