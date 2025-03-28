import pandas as pd
from typing import Tuple, Dict, Any, List
from arcgis.gis import GIS
from arcgis.geocoding import geocode
from arcgis.geometry import Geometry
from arcgis.features import FeatureLayer
from geopy.distance import geodesic

from src.logger import Logger
from src.db_helper import DBHelper


class GeoHelper:
    def __init__(self):
        self.logger = Logger()
        self.db_helper = DBHelper()

    def find_nearby_food_assistance(
        self,
        address: str,
        radius_miles: int = 10,
    ) -> pd.DataFrame:
        # Connect to CAFB's ArcGIS portal anonymously
        gis = GIS()

        # Geocode the input address
        geocoded = geocode(address)[0]
        lat = geocoded['location']['y']
        lon = geocoded['location']['x']
        print(f"Geocoded {address} to lat: {lat}, lon: {lon}")

        # Access CAFB's food assistance layer (identified from iframe analysis)
        # layer_url = "https://services.arcgis.com/su9ryhqQb8iyeiN2/arcgis/rest/services/CAFB_Partner_Locator/FeatureServer/0"
        layer_url = (
            "https://services.arcgis.com/oCjyzxNy34f0pJCV/"
            "arcgis/rest/services/Active_Agencies_Last_45_Days/FeatureServer/0"
        )
        layer = FeatureLayer(layer_url)

        # Create search geometry with buffer
        """
        What does this mean? WKID = Well-Known ID, 4326 is for WGS 84 

        What is WGS 84? 
        WGS 84 is a standard for use in cartography, geodesy, and navigation including GPS.
        It defines a reference frame for the Earth, including its shape, size, and gravitational field.
        It is the coordinate system used by GPS.

        https://en.wikipedia.org/wiki/World_Geodetic_System
        https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm
        https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm#point
        https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm#geometry-objects
        https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm#geometry-objects
        https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm#point
        https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm#geometry-objects  
        """
        search_geometry = Geometry({
            "x": lon,
            "y": lat,
            "spatialReference": {"wkid": 4326}
        })

        # Query parameters
        params = {
            'geometry': search_geometry,
            'geometryType': 'esriGeometryPoint',
            'spatialRel': 'esriSpatialRelIntersects',
            'distance': radius_miles,
            'units': 'esriSRUnit_StatuteMile',
            'returnGeometry': True,
            'outFields': 'Name, Address, City, State, ZIP, Hours, Phone, Service_Type'
        }

        # Execute query
        results = layer.query(params=params)

        # Process and sort results by distance
        final_results = []
        for feature in results:
            props = feature.attributes
            # geom = feature.geometry
            # print(f"Processing feature: {props}")
            # print(f"Feature geometry: {geom}")
            geom = {
                'x': props['longitude'],
                'y': props['latitude']
            }
            distance = geodesic((lat, lon), (geom['y'], geom['x'])).miles
            props['Distance'] = round(distance, 2)
            if props['Distance'] <= radius_miles:
                final_results.append(props)

        return sorted(final_results, key=lambda x: x['Distance'])


    # def parse_address(self, address: str) -> Tuple[float, float]:
    #     """
    #     Parse address into (latitude, longitude)
    #     Note: Order is (lat, lon) as this is the standard order used by most geopy functions
    #     """
    #     try:
    #         location = self.geocoder.geocode(address)
    #         if location:
    #             return (location.latitude, location.longitude)
    #         raise ValueError(f"Could not geocode address: {address}")
    #     except Exception as e:
    #         self.logger.error(f"Error parsing address: {str(e)}")
    #         raise
            
    # def create_circle_polygon(self, center: Tuple[float, float], radius_km: float) -> Polygon:
    #     """
    #     Create a circular polygon with given radius
    #     """
    #     try:
    #         # Create points in a circle
    #         points = []
    #         for angle in np.linspace(0, 360, 100):
    #             # Calculate point on circle using geodesic distance
    #             point = geodesic(kilometers=radius_km).destination(
    #                 Point(center), 
    #                 angle
    #             )
    #             points.append((point.longitude, point.latitude))
            
    #         # Create polygon
    #         return Polygon(points)
    #     except Exception as e:
    #         self.logger.error(f"Error creating circle polygon: {str(e)}")
    #         raise
            
    # def is_in_polygon(self, point: Tuple[float, float], polygon: Polygon) -> bool:
    #     """
    #     Check if a point is inside the polygon
    #     """
    #     try:
    #         return polygon.contains(Point(point[1], point[0]))  # Note: Shapely uses (x,y) = (lon,lat)
    #     except Exception as e:
    #         self.logger.error(f"Error checking point in polygon: {str(e)}")
    #         raise
            
    # def filter_stores_by_distance(
    #     self, 
    #     stores: List[Dict[str, Any]], 
    #     user_location: Tuple[float, float],
    #     max_distance_km: float
    # ) -> List[Dict[str, Any]]:
    #     """
    #     Filter stores by distance and sort them
    #     """
    #     try:
    #         # Create circle polygon
    #         polygon = self.create_circle_polygon(user_location, max_distance_km)
            
    #         # Filter and sort stores
    #         filtered_stores = []
    #         for store in stores:
    #             store_location = self.parse_address(store['address'])
    #             if self.is_in_polygon(store_location, polygon):
    #                 # Calculate distance
    #                 distance = geodesic(user_location, store_location).kilometers
    #                 store['distance'] = distance
    #                 filtered_stores.append(store)
            
    #         # Sort by distance
    #         return sorted(filtered_stores, key=lambda x: x['distance'])
    #     except Exception as e:
    #         self.logger.error(f"Error filtering stores by distance: {str(e)}")
    #         raise
            
    # def update_store_location(self, store_id: str, address: str) -> bool:
    #     """
    #     Update store location in the database
    #     """
    #     try:
    #         # Parse address to coordinates
    #         coordinates = self.parse_address(address)
            
    #         # Store in database
    #         return self.db_helper.update_store_location(
    #             store_id,
    #             coordinates[0],  # latitude
    #             coordinates[1]   # longitude
    #         )
    #     except Exception as e:
    #         self.logger.error(f"Error updating store location: {str(e)}")
    #         raise
            
    # def batch_update_store_locations(
    #     self,
    #     store_locations: List[Dict[str, str]]
    # ) -> bool:
    #     """
    #     Batch update store locations
    #     """
    #     try:
    #         for store_data in store_locations:
    #             store_id = store_data.get('id')
    #             address = store_data.get('address')
    #             if store_id and address:
    #                 self.update_store_location(store_id, address)
    #         return True
    #     except Exception as e:
    #         self.logger.error(f"Error batch updating store locations: {str(e)}")
    #         raise
            
    # def calculate_distance_matrix(
    #     self,
    #     locations: List[Tuple[float, float]]
    # ) -> np.ndarray:
    #     """
    #     Calculate distance matrix between multiple locations
    #     """
    #     try:
    #         n = len(locations)
    #         matrix = np.zeros((n, n))
            
    #         for i in range(n):
    #             for j in range(i + 1, n):
    #                 distance = geodesic(locations[i], locations[j]).kilometers
    #                 matrix[i, j] = distance
    #                 matrix[j, i] = distance
                    
    #         return matrix
    #     except Exception as e:
    #         self.logger.error(f"Error calculating distance matrix: {str(e)}")
    #         raise 

# from typing import Dict, Any, List, Tuple
# import geopy
# from geopy.geocoders import Nominatim
# from geopy.distance import geodesic
# from shapely.geometry import Point, Polygon
# import numpy as np
# from src.logger import Logger
# from src.db_helper import DBHelper

# class GeoHelper:
#     def __init__(self):
#         self.logger = Logger()
#         self.geocoder = Nominatim(user_agent="ai_la_carte")
#         self.db_helper = DBHelper()
        
#     def parse_address(self, address: str) -> Tuple[float, float]:
#         """
#         Parse address into (latitude, longitude)
#         Note: Order is (lat, lon) as this is the standard order used by most geopy functions
#         """
#         try:
#             location = self.geocoder.geocode(address)
#             if location:
#                 return (location.latitude, location.longitude)
#             raise ValueError(f"Could not geocode address: {address}")
#         except Exception as e:
#             self.logger.error(f"Error parsing address: {str(e)}")
#             raise
            
#     def create_circle_polygon(self, center: Tuple[float, float], radius_km: float) -> Polygon:
#         """
#         Create a circular polygon with given radius
#         """
#         try:
#             # Create points in a circle
#             points = []
#             for angle in np.linspace(0, 360, 100):
#                 # Calculate point on circle using geodesic distance
#                 point = geodesic(kilometers=radius_km).destination(
#                     Point(center), 
#                     angle
#                 )
#                 points.append((point.longitude, point.latitude))
            
#             # Create polygon
#             return Polygon(points)
#         except Exception as e:
#             self.logger.error(f"Error creating circle polygon: {str(e)}")
#             raise
            
#     def is_in_polygon(self, point: Tuple[float, float], polygon: Polygon) -> bool:
#         """
#         Check if a point is inside the polygon
#         """
#         try:
#             return polygon.contains(Point(point[1], point[0]))  # Note: Shapely uses (x,y) = (lon,lat)
#         except Exception as e:
#             self.logger.error(f"Error checking point in polygon: {str(e)}")
#             raise
            
#     def filter_stores_by_distance(
#         self, 
#         stores: List[Dict[str, Any]], 
#         user_location: Tuple[float, float],
#         max_distance_km: float
#     ) -> List[Dict[str, Any]]:
#         """
#         Filter stores by distance and sort them
#         """
#         try:
#             # Create circle polygon
#             polygon = self.create_circle_polygon(user_location, max_distance_km)
            
#             # Filter and sort stores
#             filtered_stores = []
#             for store in stores:
#                 store_location = self.parse_address(store['address'])
#                 if self.is_in_polygon(store_location, polygon):
#                     # Calculate distance
#                     distance = geodesic(user_location, store_location).kilometers
#                     store['distance'] = distance
#                     filtered_stores.append(store)
            
#             # Sort by distance
#             return sorted(filtered_stores, key=lambda x: x['distance'])
#         except Exception as e:
#             self.logger.error(f"Error filtering stores by distance: {str(e)}")
#             raise
            
#     def update_store_location(self, store_id: str, address: str) -> bool:
#         """
#         Update store location in the database
#         """
#         try:
#             # Parse address to coordinates
#             coordinates = self.parse_address(address)
            
#             # Store in database
#             return self.db_helper.update_store_location(
#                 store_id,
#                 coordinates[0],  # latitude
#                 coordinates[1]   # longitude
#             )
#         except Exception as e:
#             self.logger.error(f"Error updating store location: {str(e)}")
#             raise
            
#     def batch_update_store_locations(
#         self,
#         store_locations: List[Dict[str, str]]
#     ) -> bool:
#         """
#         Batch update store locations
#         """
#         try:
#             for store_data in store_locations:
#                 store_id = store_data.get('id')
#                 address = store_data.get('address')
#                 if store_id and address:
#                     self.update_store_location(store_id, address)
#             return True
#         except Exception as e:
#             self.logger.error(f"Error batch updating store locations: {str(e)}")
#             raise
            
#     def calculate_distance_matrix(
#         self,
#         locations: List[Tuple[float, float]]
#     ) -> np.ndarray:
#         """
#         Calculate distance matrix between multiple locations
#         """
#         try:
#             n = len(locations)
#             matrix = np.zeros((n, n))
            
#             for i in range(n):
#                 for j in range(i + 1, n):
#                     distance = geodesic(locations[i], locations[j]).kilometers
#                     matrix[i, j] = distance
#                     matrix[j, i] = distance
                    
#             return matrix
#         except Exception as e:
#             self.logger.error(f"Error calculating distance matrix: {str(e)}")
#             raise 