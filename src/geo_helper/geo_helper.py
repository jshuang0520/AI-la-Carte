from typing import Dict, Any, List, Tuple
import geopy
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon
import numpy as np
from src.logger import Logger

class GeoHelper:
    def __init__(self):
        self.logger = Logger()
        self.geocoder = Nominatim(user_agent="ai_la_carte")
        
    def parse_address(self, address: str) -> Tuple[float, float]:
        """
        Parse address into (latitude, longitude)
        Note: Order is (lat, lon) as this is the standard order used by most geopy functions
        """
        try:
            location = self.geocoder.geocode(address)
            if location:
                return (location.latitude, location.longitude)
            raise ValueError(f"Could not geocode address: {address}")
        except Exception as e:
            self.logger.error(f"Error parsing address: {str(e)}")
            raise
            
    def create_circle_polygon(self, center: Tuple[float, float], radius_km: float) -> Polygon:
        """
        Create a circular polygon with given radius
        """
        try:
            # Create points in a circle
            points = []
            for angle in np.linspace(0, 360, 100):
                # Calculate point on circle using geodesic distance
                point = geodesic(kilometers=radius_km).destination(
                    Point(center), 
                    angle
                )
                points.append((point.longitude, point.latitude))
            
            # Create polygon
            return Polygon(points)
        except Exception as e:
            self.logger.error(f"Error creating circle polygon: {str(e)}")
            raise
            
    def is_in_polygon(self, point: Tuple[float, float], polygon: Polygon) -> bool:
        """
        Check if a point is inside the polygon
        """
        try:
            return polygon.contains(Point(point[1], point[0]))  # Note: Shapely uses (x,y) = (lon,lat)
        except Exception as e:
            self.logger.error(f"Error checking point in polygon: {str(e)}")
            raise
            
    def filter_stores_by_distance(
        self, 
        stores: List[Dict[str, Any]], 
        user_location: Tuple[float, float],
        max_distance_km: float
    ) -> List[Dict[str, Any]]:
        """
        Filter stores by distance and sort them
        """
        try:
            # Create circle polygon
            polygon = self.create_circle_polygon(user_location, max_distance_km)
            
            # Filter and sort stores
            filtered_stores = []
            for store in stores:
                store_location = self.parse_address(store['address'])
                if self.is_in_polygon(store_location, polygon):
                    # Calculate distance
                    distance = geodesic(user_location, store_location).kilometers
                    store['distance'] = distance
                    filtered_stores.append(store)
            
            # Sort by distance
            return sorted(filtered_stores, key=lambda x: x['distance'])
        except Exception as e:
            self.logger.error(f"Error filtering stores by distance: {str(e)}")
            raise 