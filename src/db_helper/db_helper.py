from typing import Any, Dict, List
import os
import pandas as pd
import numpy as np
from src.utilities.logger import Logger
from src.utilities.config_parser import load_config

class DBHelper:
    def __init__(self, user_prefs: Dict[str, Any] = None):
        self.logger = Logger()
        self.config = load_config()
        self.data_dir = "data"
        self.documents = {}
        self.embeddings = {}
        self.user_prefs = user_prefs
        self._load_data()
        
    def _load_data(self):
        """
        Load all Excel files from data directory and process them into documents
        """
        try:
            # Define the Excel file paths
            files = {
                "CAFB_Markets_Shopping_Partners": "CAFB_Markets_Shopping_Partners.xlsx",
            }
            
            # Load each Excel file
            self.raw_data = {}
            for name, filename in files.items():
                filepath = os.path.join(self.data_dir, filename)
                if os.path.exists(filepath):
                    df = pd.read_excel(filepath)
                    self.raw_data[name] = df
                    self.logger.info(f"Loaded {name} with shape {df.shape}")
                else:
                    self.logger.warning(f"File not found: {filepath}")
                    
            # Process data into documents
            self._process_data()
            
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise
            
    def _process_data(self):
        """
        Process raw data into documents suitable for RAG
        """
        try:
            # Process Markets data
            cafb_docs = []
            
            # Process each market and Shopping Partner
            markets_sp = self.raw_data.get("CAFB_Markets_Shopping_Partners", pd.DataFrame())
            for _, market in markets_sp.iterrows():
                doc = {
                    "id": market["Agency ID"],
                    "name": market["Agency Name"],
                    "type": "Shopping Partner" if "PART" in market["Agency ID"] else "Market",
                    "status": market["Status"],
                    "region": market["Agency Region"],
                    "county": market["County/Ward"],
                    "address": market["Shipping Address"],
                    "phone": market["Phone"],
                    "website": market["URL"],
                    "hours": {
                        "day": market["Day or Week"],
                        "start": market["Starting Time"],
                        "end": market["Ending Time"],
                        "frequency": market["Frequency"]
                    },
                    "requirements": market["Food Pantry Requirements"],
                    "format": market["Food Format "],
                    "choice_options": market["Choice Options"],
                    "distribution": market["Distribution Models"],
                    "appointment_required": market["By Appointment Only"],
                    "additional_hours_info": market["Additional Note on Hours of Operations"],
                    "cultures_served": market["Cultural Populations Served"].tolist(),
                    "services": market["Wraparound Service"].tolist()
                }
                cafb_docs.append(doc)

            # Store all documents
            self.documents = {
                "markets": cafb_docs,
                "geo_data": self.user_prefs.get("geo_data", [])
            }
            
        except Exception as e:
            self.logger.error(f"Error processing data: {str(e)}")
            raise
            
    def store_embeddings(self, doc_id: str, embeddings: np.ndarray):
        """
        Store embeddings for a document
        """
        self.embeddings[doc_id] = embeddings
        
    def get_documents(self, doc_type: str = None) -> List[Dict[str, Any]]:
        """
        Get all documents, optionally filtered by type
        """
        if doc_type == "markets":
            return self.documents["markets"]
        elif doc_type == "partners":
            return self.documents["partners"]
        else:
            return self.documents["markets"] + self.documents["partners"]
            
    def get_document_by_id(self, doc_id: str) -> Dict[str, Any]:
        """
        Get a specific document by ID
        """
        for doc in self.get_documents():
            if doc["id"] == doc_id:
                return doc
        return None
        
    def get_embeddings(self, doc_id: str = None) -> Dict[str, np.ndarray]:
        """
        Get embeddings, either for a specific document or all documents
        """
        if doc_id:
            return self.embeddings.get(doc_id)
        return self.embeddings 