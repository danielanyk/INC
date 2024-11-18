import time
import csv 
import math
import itertools
import matplotlib.pyplot as plt

class Finder:
    def __init__(self, csv_file):
        """
        Initialize the Finder with a CSV file path.
        
        Parameters:
        csv_file (str): The path to the CSV file containing road data.
        """
        self.csv_file = csv_file
        self.roads = self.load_roads(self.csv_file)

    def load_roads(self, csv_file):
        """
        Load roads data from a CSV file.
        
        Parameters:
        csv_file (str): The path to the CSV file containing road data.
        
        Returns:
        list: A list of dictionaries, each representing a road with its attributes.
        """
        roads = []
        with open(csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                road = {
                    'name': row['RoadName'],
                    "category": row["RoadCategory"],
                    'start_lat': float(row['StartLat']),
                    'start_lon': float(row['StartLon']),
                    'end_lat': float(row['EndLat']),
                    'end_lon': float(row['EndLon'])
                }
                roads.append(road)
        return roads
    
    def haversine(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great-circle distance between two points on the Earth's surface using the Haversine formula.
        
        The Haversine formula is an equation that can be used to find the shortest distance between two points on a sphere, given their longitudes and latitudes. The formula is particularly useful in navigation and geographic information systems (GIS).
    
        Parameters:
        lat1 (float): Latitude of the first point in decimal degrees.
        lon1 (float): Longitude of the first point in decimal degrees.
        lat2 (float): Latitude of the second point in decimal degrees.
        lon2 (float): Longitude of the second point in decimal degrees.
    
        Returns:
        float: The distance between the two points in kilometers.
    
        The formula to calculate distance (d) is:
        d = 2 * R * asin(sqrt(hav(dlat) + cos(lat1) * cos(lat2) * hav(dlon)))
    
        where:
        - R is the Earth's radius (mean radius = 6,371 km)
        - hav is the haversine function: hav(theta) = sin²(theta / 2)
        - dlat = lat2 - lat1 (difference in latitude)
        - dlon = lon2 - lon1 (difference in longitude)
        """
        R = 6371  # Earth radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def point_to_segment_distance(self, lat, lon, lat1, lon1, lat2, lon2):
        """
        Calculate the shortest distance from a point to a line segment.
        
        Parameters:
        lat (float): Latitude of the point.
        lon (float): Longitude of the point.
        lat1 (float): Latitude of the first endpoint of the line segment.
        lon1 (float): Longitude of the first endpoint of the line segment.
        lat2 (float): Latitude of the second endpoint of the line segment.
        lon2 (float): Longitude of the second endpoint of the line segment.
        
        Returns:
        float: The shortest distance from the point to the line segment in kilometers.
        """
        A = (lat - lat1, lon - lon1)
        B = (lat2 - lat1, lon2 - lon1)
        B_len = math.hypot(*B)
        B_unit = (B[0] / B_len, B[1] / B_len)
        A_proj = A[0] * B_unit[0] + A[1] * B_unit[1]
        if A_proj <= 0:
            return self.haversine(lat, lon, lat1, lon1)
        elif A_proj >= B_len:
            return self.haversine(lat, lon, lat2, lon2)
        else:
            closest = (lat1 + B_unit[0] * A_proj, lon1 + B_unit[1] * A_proj)
            return self.haversine(lat, lon, closest[0], closest[1])

    def find_closest_road(self, lat, lon):
        """
        Find the closest road to a given latitude and longitude.
        
        Parameters:
        lat (float): Latitude of the point.
        lon (float): Longitude of the point.
        
        Returns:
        tuple: The latitude, longitude, name, and category of the closest road.
        """
        closest_road = None
        min_distance = float('inf')
        for road in self.roads:
            distance = self.point_to_segment_distance(lat, lon, road['start_lat'], road['start_lon'], road['end_lat'], road['end_lon'])
            if distance < min_distance:
                min_distance = distance
                closest_road = road
        return lat, lon, closest_road["name"], closest_road["category"]
    

if __name__ == "__main__":
    # Example usage
    new_finder = Finder('../../Roads.csv')
    print(new_finder.find_closest_road(1.301844, 103.846272))
