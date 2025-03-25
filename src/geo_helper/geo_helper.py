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
