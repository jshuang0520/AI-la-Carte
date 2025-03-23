from typing import Any, Dict, List
import sqlite3
import numpy as np
from src.logger import Logger
from src.config import Config

class DBHelper:
    def __init__(self):
        self.logger = Logger()
        self.config = Config()
        self.db_path = self.config.get_db_path()
        
    def connect(self):
        """
        Create database connection
        """
        try:
            return sqlite3.connect(self.db_path)
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise
            
    def store_data(self, data: Dict[str, Any], language: str) -> bool:
        """
        Store data in the database
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # TODO: Implement actual storage logic
            # This is a placeholder implementation
            cursor.execute("""
                INSERT INTO data (content, language)
                VALUES (?, ?)
            """, (str(data), language))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Error storing data: {str(e)}")
            raise
            
    def retrieve_data(self, language: str) -> List[Dict[str, Any]]:
        """
        Retrieve data from the database
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # TODO: Implement actual retrieval logic
            # This is a placeholder implementation
            cursor.execute("""
                SELECT content FROM data
                WHERE language = ?
            """, (language,))
            
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            self.logger.error(f"Error retrieving data: {str(e)}")
            raise

    def get_store_embeddings(self) -> List[Dict[str, Any]]:
        """
        Retrieve store embeddings from the database
        Returns a list of dictionaries containing store details and their embeddings
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT store_id, name, address, embedding
                FROM store_embeddings
            """)
            
            results = cursor.fetchall()
            store_embeddings = []
            
            for row in results:
                store_id, name, address, embedding = row
                # Convert string representation of embedding back to numpy array
                embedding_array = np.frombuffer(embedding, dtype=np.float32)
                store_embeddings.append({
                    'store_id': store_id,
                    'name': name,
                    'address': address,
                    'embedding': embedding_array
                })
            
            conn.close()
            return store_embeddings
        except Exception as e:
            self.logger.error(f"Error retrieving store embeddings: {str(e)}")
            raise 