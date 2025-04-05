from typing import Any, Dict, List
import os
import pandas as pd
import numpy as np
from src.logger import Logger
from src.utilities import Config

class DBHelper:
    def __init__(self):
        self.logger = Logger()
        self.config = Config()
        self.data_dir = "data"
        self.documents = {}
        self.embeddings = {}
        self._load_data()
        
    def _load_data(self):
        """
        Load all Excel files from data directory and process them into documents
        """
        try:
            # Define the Excel file paths
            files = {
                "CAFB_Markets_Cultures_Served": "CAFB_Markets_Cultures_Served.xlsx",
                "CAFB_Markets_HOO": "CAFB_Markets_HOO.xlsx",
                "CAFB_Markets_Wraparound_Services": "CAFB_Markets_Wraparound_Services.xlsx",
                "CAFB_Shopping_Partners_Cultures_Served": "CAFB_Shopping_Partners_Cultures_Served.xlsx",
                "CAFB_Shopping_Partners_HOO": "CAFB_Shopping_Partners_HOO.xlsx",
                "CAFB_Shopping_Partners_Wraparound_Services": "CAFB_Shopping_Partners_Wraparound_Services.xlsx"
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
            markets_docs = []
            
            # Combine Markets data
            if all(k in self.raw_data for k in ["CAFB_Markets_HOO", "CAFB_Markets_Cultures_Served", "CAFB_Markets_Wraparound_Services"]):
                markets_hoo = self.raw_data["CAFB_Markets_HOO"]
                markets_cultures = self.raw_data["CAFB_Markets_Cultures_Served"]
                markets_services = self.raw_data["CAFB_Markets_Wraparound_Services"]
                
                # Process each market
                for _, market in markets_hoo.iterrows():
                    doc = {
                        "id": market["Agency ID"],
                        "name": market["Agency Name"],
                        "type": "Market",
                        "address": market["Shipping Address"],
                        "hours": {
                            "day": market["Day or Week"],
                            "start": market["Starting Time"],
                            "end": market["Ending Time"],
                            "frequency": market["Frequency"]
                        },
                        "requirements": market["Food Pantry Requirements"],
                        "format": market["Food Format "],
                        "distribution": market["Distribution Models"],
                        "cultures_served": markets_cultures[
                            markets_cultures["Agency ID"] == market["Agency ID"]
                        ]["Cultural Populations Served"].tolist(),
                        "services": markets_services[
                            markets_services["Agency ID"] == market["Agency ID"]
                        ]["Wraparound Service"].tolist()
                    }
                    markets_docs.append(doc)
                    
            # Process Shopping Partners data
            partners_docs = []
            
            # Combine Partners data
            if all(k in self.raw_data for k in ["CAFB_Shopping_Partners_HOO", "CAFB_Shopping_Partners_Cultures_Served", "CAFB_Shopping_Partners_Wraparound_Services"]):
                partners_hoo = self.raw_data["CAFB_Shopping_Partners_HOO"]
                partners_cultures = self.raw_data["CAFB_Shopping_Partners_Cultures_Served"]
                partners_services = self.raw_data["CAFB_Shopping_Partners_Wraparound_Services"]
                
                # Process each partner
                for _, partner in partners_hoo.iterrows():
                    doc = {
                        "id": partner["External ID"],
                        "name": partner["Name"],
                        "type": "Shopping Partner",
                        "status": partner["Status"],
                        "region": partner["Agency Region"],
                        "county": partner["County/Ward"],
                        "address": partner["Shipping Address"],
                        "phone": partner["Phone"],
                        "hours": {
                            "day": partner["Day or Week"],
                            "monthly_options": partner["Monthly Options"],
                            "start": partner["Starting Time"],
                            "end": partner["Ending Time"],
                            "appointment_only": partner["By Appointment Only"]
                        },
                        "requirements": partner["Food Pantry Requirements"],
                        "distribution": partner["Distribution Models"],
                        "format": partner["Food Format "],
                        "additional_hours_info": partner["Additional Note on Hours of Operations"],
                        "cultures_served": partners_cultures[
                            partners_cultures["Agency ID"] == partner["External ID"]
                        ]["Cultural Populations Served"].tolist(),
                        "services": partners_services[
                            partners_services["Agency ID"] == partner["External ID"]
                        ]["Wraparound Service"].tolist()
                    }
                    partners_docs.append(doc)
                    
            # Store all documents
            self.documents = {
                "markets": markets_docs,
                "partners": partners_docs
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