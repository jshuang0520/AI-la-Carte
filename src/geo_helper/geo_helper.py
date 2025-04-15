import pandas as pd
import os
from typing import Tuple, Dict, Any, List
from arcgis.gis import GIS
from arcgis.geocoding import geocode
from arcgis.geometry import Geometry
from arcgis.features import FeatureLayer
from geopy.distance import geodesic

from src.utilities.logger import Logger

class GeoHelper:
    def __init__(self):
        self.logger = Logger()

    def find_nearby_food_assistance(
        self,
        address: str,
        radius_miles: int = None,
        limit: int = None
    ) -> pd.DataFrame:
        """
        Find nearby food assistance locations using CAFB's ArcGIS portal.
        """
        project_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.logger.info(f"Finding nearby food assistance for address: {address}")
        # Connect to CAFB's ArcGIS portal anonymously
        gis = GIS()

        # Geocode the input address
        geocoded = geocode(address)[0]
        lat = geocoded['location']['y']
        lon = geocoded['location']['x']
        self.logger.info(
            f"Geocoded {address} to lat: {lat}, lon: {lon} with confidence: {geocoded['score']}"
        )

        # Access CAFB food data, sort and filter
        data = pd.read_excel(
            os.path.join(project_dir, 'data', 'CAFB_Markets_Shopping_Partners.xlsx')
        )
        data["Distance"] = data.apply(
            lambda x: geodesic((lat, lon), (x["y"], x["x"])).miles, axis=1
        )
        data = data.sort_values(by="Distance").reset_index(drop=True)
        if radius_miles is not None:
            data = data[data["Distance"] <= radius_miles].drop_duplicates()
        data = data[["Agency ID", "Agency Name", "Distance"]].drop_duplicates()

        self.logger.info(f"Found {data.shape[0]} nearby food assistance locations.")
        if limit is None:
            return data.to_dict(orient='records')
        else: 
            return data.head(limit).to_dict(orient='records')