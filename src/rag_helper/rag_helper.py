from typing import Dict, Any, List
from src.logger import Logger
from src.embedding_helper import EmbeddingHelper
from src.db_helper import DBHelper
from src.translate_helper import TranslateHelper
import numpy as np

class RAGHelper:
    def __init__(self):
        self.logger = Logger()
        self.embedding_helper = EmbeddingHelper()
        self.db_helper = DBHelper()
        self.translate_helper = TranslateHelper()
        
    def create_prompt_template(self, user_preferences: Dict[str, Any]) -> str:
        """
        Create a prompt template for RAG based on user preferences
        """
        try:
            # Translate preferences to English for processing
            en_preferences = self.translate_helper.translate_to_english(str(user_preferences))
            
            template = f"""
            Based on the following user preferences:
            {en_preferences}
            
            Please recommend stores that best match these requirements.
            Consider:
            1. Food requirements and restrictions
            2. Available time slots
            3. Store specialties and offerings
            
            Return the top N most relevant stores with their details.
            """
            return template
        except Exception as e:
            self.logger.error(f"Error creating prompt template: {str(e)}")
            raise
            
    def format_prompt(self, template: str, user_preferences: Dict[str, Any]) -> str:
        """
        Format the prompt template with user preferences
        """
        try:
            # Add specific formatting based on preferences
            formatted_prompt = template.replace(
                "{preferences}", 
                str(user_preferences)
            )
            return formatted_prompt
        except Exception as e:
            self.logger.error(f"Error formatting prompt: {str(e)}")
            raise
            
    def perform_rag(self, prompt: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Perform RAG to find relevant stores
        """
        try:
            # Get store embeddings from database
            store_embeddings = self.db_helper.get_store_embeddings()
            
            # Create embedding for the prompt
            prompt_embedding = self.embedding_helper.create_embedding(prompt)
            
            # Calculate similarities and get top N stores
            similarities = []
            for store_id, store_embedding in store_embeddings.items():
                similarity = self.embedding_helper.compute_similarity(
                    prompt_embedding,
                    store_embedding
                )
                similarities.append((store_id, similarity))
            
            # Sort by similarity and get top N
            top_stores = sorted(similarities, key=lambda x: x[1], reverse=True)[:top_n]
            
            # Get store details from database
            store_details = self.db_helper.get_store_details([store_id for store_id, _ in top_stores])
            
            return store_details
        except Exception as e:
            self.logger.error(f"Error performing RAG: {str(e)}")
            raise
            
    def update_store_embeddings(self, store_id: str, store_data: Dict[str, Any]) -> bool:
        """
        Update store embeddings in the database
        """
        try:
            # Create embedding for store data
            store_embedding = self.embedding_helper.create_embedding(str(store_data))
            
            # Store in database
            return self.db_helper.update_store_embedding(store_id, store_embedding)
        except Exception as e:
            self.logger.error(f"Error updating store embeddings: {str(e)}")
            raise
            
    def batch_update_store_embeddings(
        self,
        store_data_list: List[Dict[str, Any]]
    ) -> bool:
        """
        Batch update store embeddings
        """
        try:
            for store_data in store_data_list:
                store_id = store_data.get('id')
                if store_id:
                    self.update_store_embeddings(store_id, store_data)
            return True
        except Exception as e:
            self.logger.error(f"Error batch updating store embeddings: {str(e)}")
            raise 