import pandas as pd
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
        radius_miles: int = 10,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Find nearby food assistance locations using CAFB's ArcGIS portal.
        """
        self.logger.info(f"Finding nearby food assistance for address: {address}")
        # Connect to CAFB's ArcGIS portal anonymously
        gis = GIS()

        # Geocode the input address
        geocoded = geocode(address)[0]
        lat = geocoded['location']['y']
        lon = geocoded['location']['x']
        self.logger.info(f"Geocoded {address} to lat: {lat}, lon: {lon}")

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
            geom = {
                'x': props['longitude'],
                'y': props['latitude']
            }
            if not props["agency_ref"]:
                continue
            distance = geodesic((lat, lon), (geom['y'], geom['x'])).miles
            temp_dict = {
                'Distance': round(distance, 2),
                'agency_ref': props.get('agency_ref', None),
                'name': props.get('name', None),
            }
            if distance <= radius_miles:
                final_results.append(temp_dict)

        sorted_final_results = sorted(final_results, key=lambda x: x['Distance'])
        self.logger.info(f"Found {len(sorted_final_results)} nearby food assistance locations.")

        return sorted_final_results[:min(limit, len(sorted_final_results))]