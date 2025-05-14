import pandas as pd
from shapely.geometry import LineString, Point


class RoadTypeMapper:
    def __init__(self, csv_path):
        self.road_df = pd.read_csv(csv_path)

        self.road_df["geometry"] = self.road_df.apply(
            lambda row: LineString(
                [(row["StartLon"], row["StartLat"]), (row["EndLon"], row["EndLat"])]
            ),
            axis=1,
        )

    def get_road_type(self, latitude, longitude, max_distance=0.0003):
        point = Point(longitude, latitude)

        closest = None
        min_distance = float("inf")

        for _, row in self.road_df.iterrows():
            dist = point.distance(row["geometry"])
            if dist < min_distance and dist <= max_distance:
                min_distance = dist
                closest = row["RoadCategory"]

        return closest or "Unknown"
