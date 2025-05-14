# ------------------
# Description
# ------------------
# Retrieve relevant DB data in GeoJSON format using PyMongo

# ------------------
# Imports
# ------------------
import os, shutil
import pymongo
import geopandas as gpd
from datetime import datetime
from qgis.core import QgsProject

# ------------------
# MongoDB Setup
# ------------------
# Connect to MongoDB Database
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["FYP"]

# ------------------
# Directories
# ------------------
# Store string of inspection dates for grouping
current_directory = os.getcwd() # shld be C:\Users\...\...\fyp_teampink\A_QGIS
data_path = f"{current_directory}/MongoDB Connection/data"
latestBatchData_path = data_path + "/Latest Batch"
inspectionDateData_path = data_path + "/Inspection Dates"
all_defect_path = data_path + "/All Merged"

# ------------------
# QGIS Settings
# ------------------
# Reference root of layer tree in current qgis project
root = QgsProject.instance().layerTreeRoot()

# ---------------------------------------
# Functions - MongoDB Aggregation Queries
# ---------------------------------------
# ------------------------
# save_geoJson_file Function
# ------------------------
def save_geoJson_file(geojson_data, file_path, file_name):
    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])
    # Write the GeoDataFrame to a GeoJSON file
    geoJson_path = file_path + f"/{file_name}.geojson"
    gdf.to_file(geoJson_path, driver="GeoJSON")
    return geoJson_path

# ------------------------
# get_latestBatch Function
# ------------------------
def get_latestBatch():
    try:
        # Aggregate Pipepline
        # * Get datetime in the correct format to calculate batch processing duration
        latestBatch_pipeline = [
            # Stage 1: Get latest batchID
            {"$sort" : {"batchID" : -1}},
            {"$limit" : 1},
            # Stage 2: Get images associated with latest batchID
            {"$lookup" : {
                "from" : "batchImage",
                "localField" : "batchID",
                "foreignField": "batchID",
                "as" : "latestImages" # name of new array field to add matching documents from "from" collection
            }},
            {"$unwind": "$latestImages"}, # deconstruct array field into object for each element
            # Stage 3: Get latest image details
            {"$lookup": {
                "from": "image",
                "localField": "latestImages.imageID",
                "foreignField": "imageID",
                "as": "imageDetails"
            }},
            {"$unwind": "$imageDetails"}, # deconstruct array field into object
            # Stage 4: Get defects associated with each latest image
            {"$lookup" : {
                "from" : "defect",
                "localField" : "latestImages.imageID",
                "foreignField" : "imageID",
                "as" : "latestDefects" # name of new array field to add matching documents from "from" collection
            }},
            {"$unwind": { # deconstruct array field into object
                "path" : "$latestDefects",
                "preserveNullAndEmptyArrays" : True # keep images that do not have defects
            }}, 
            # Stage 5: Project fields
            {"$project": {
                'batchID': 1,
                'status': 1,
                'totalFrames': 1,
                'framesProcessed': 1,
                'batchStartProcessing': 1,
                'batchFinishProcessing': 1,
                'imageDetails.imageID': 1,
                'imageDetails.imagePath': 1,
                'imageDetails.longitude': 1,
                'imageDetails.latitude': 1,
                'imageDetails.datetime': 1,
                'imageDetails.town': 1,
                'imageDetails.road': 1,
                'imageDetails.roadType': 1,
                'latestDefects.defectID': 1,
                'latestDefects.outputLabel': 1,
                'latestDefects.severity': 1,
                'latestDefects.confidence': 1,
                '_id': 0
            }}
        ]
        latestBatch_data = db["batch"].aggregate(latestBatch_pipeline)

        # Store in GeoJSON format
        latestBatch_geoJson = {
            "type": "FeatureCollection",
            "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
            "features" : []
        }

        latestBatchDefect_geoJson = {
            "type": "FeatureCollection",
            "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
            "features" : []
        }

        latestBatchNonDefect_geoJson = {
            "type": "FeatureCollection",
            "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
            "features" : []
        }

        # Retrieve data from mongodb output
        for document in list(latestBatch_data):
            # Condition to check if image has any associated defects
            defect_Condition = "latestDefects" in document
            # Write into Feature
            feature = {
                "type": "Feature",
                "geometry":{
                    "type":"Point",
                    "coordinates" : [document["imageDetails"]["longitude"], document["imageDetails"]["latitude"]]
                },
                "properties": {
                    "BatchID": document["batchID"],
                    "Status": document["status"],
                    "FramesProcessed": document["framesProcessed"],
                    "BatchStartProcessing": document['batchStartProcessing'],
                    "BatchFinishProcessing": document['batchFinishProcessing'],
                    "TotalFrames": document["totalFrames"],
                    "Type": document["latestDefects"]["outputLabel"] if defect_Condition else "NULL",
                    "Severity": document["latestDefects"]["severity"] if defect_Condition else "NULL",
                    "Confidence": document["latestDefects"]["confidence"] if defect_Condition else "NULL",
                    "ImageID": document["imageDetails"]["imageID"],
                    "OImagePath": document["imageDetails"]["imagePath"],
                    "DateTime": document["imageDetails"]["datetime"],
                    "Road" : document["imageDetails"]["road"],
                    "Town": document["imageDetails"]["town"],
                    "RoadType": document["imageDetails"]["roadType"],
                    "DefectID": document["latestDefects"]["defectID"] if defect_Condition else "NULL"
                    }
                }
            # Check if Defect/Non-Defect
            if defect_Condition:
                # Defect
                latestBatchDefect_geoJson["features"].append(feature)
            else:
                # Non Defect
                latestBatchNonDefect_geoJson["features"].append(feature)

            latestBatch_geoJson["features"].append(feature)

        # Make LatestBatch directory
        os.mkdir(latestBatchData_path)

        # Save to geojson file
        latest_batch_path = save_geoJson_file(latestBatch_geoJson, latestBatchData_path, "latest_batch")
        latest_batch_defect_path = save_geoJson_file(latestBatchDefect_geoJson, latestBatchData_path, "latest_batch_defect")
        latest_batch_non_path = save_geoJson_file(latestBatchNonDefect_geoJson, latestBatchData_path, "latest_batch_non_defect")
        return [latest_batch_defect_path, latest_batch_non_path, latest_batch_path]
        
    except Exception as e:
        print("Error: ", e)
        return None

# ---------------------------
# get_InspectionDate Function
# ---------------------------
def get_InspectionDate():
    try:
        # Make Inspection Date directory
        os.mkdir(inspectionDateData_path)

        # Step 1: Retrieve unique dates under "datetime" attribute from image collection
        unique_dates = db["image"].aggregate([
            {"$project": {
                "date": {"$dateToString": {"format": '%d %m %Y', "date": {"$toDate": "$datetime"}}}
            }},
            {"$group": {"_id": "$date"}}
        ])
        # Sort & format dates to present as "d m Y" e.g. "01 01 2024"
        unique_dates_list = sorted([datetime.strptime(entry["_id"], "%d %m %Y") for entry in unique_dates])
        # Convert into "d b Y" e.g. "01 Jan 2024"
        unique_dates_list = [date.strftime("%d %b %Y") for date in unique_dates_list]

        # Step 2: Retrieve ImageIDs associated with unique inspection dates
        for inspection_date in unique_dates_list:
            # Regex to match date portion before comma e.g. in mongodb "01 Jan 2024, 08:58:48"
            regex_pattern = f"^{inspection_date},"
            # Aggregate Pipepline
            inspectionDate_pipeline = [
                # Stage 1: Get images associated with specific inspection date
                {"$match": {"datetime": {"$regex": regex_pattern}}},
                # Stage 2: Get defect details associated with specific image if applicable
                {"$lookup": {
                    "from": "defect",
                    "localField": "imageID",
                    "foreignField": "imageID",
                    "as": "imageDefects" # name of new array field to add matching documents from "from" collection
                }},
                {"$unwind": { # deconstruct array field into object
                    "path" : "$imageDefects",
                    "preserveNullAndEmptyArrays" : True # keep images that do not have defects
                }},
                # Stage 3: Get batch details associated with specific image
                {"$lookup": {
                    "from": "batchImage",
                    "localField": "imageID",
                    "foreignField": "imageID",
                    "as": "imageBatchDetails" # name of new array field to add matching documents from "from" collection
                }},
                {"$unwind": "$imageBatchDetails"}, # deconstruct array field into object for each element
                # Stage 4: Get batch details associated with specific image
                {"$lookup": {
                    "from": "batch",
                    "localField": "imageBatchDetails.batchID",
                    "foreignField": "batchID",
                    "as": "batchDetails" # name of new array field to add matching documents from "from" collection
                }},
                {"$unwind": "$batchDetails"}, # deconstruct array field into object for each element
                # Stage 5: Project fields
                {"$project": {
                    'imageID': 1,
                    'imageBatchDetails.batchID': 1,
                    'imagePath': 1,
                    'longitude': 1,
                    'latitude': 1,
                    'datetime': 1,
                    'town': 1,
                    'road': 1,
                    'roadType': 1,
                    'imageDefects.defectID': 1,
                    'imageDefects.outputLabel': 1,
                    'imageDefects.severity': 1,
                    'imageDefects.confidence': 1,
                    'batchDetails.status' : 1,
                    'batchDetails.batchStartProcessing': 1,
                    'batchDetails.batchFinishProcessing': 1,
                    '_id': 0
                }}
            ]
            inspectionDate_data = db["image"].aggregate(inspectionDate_pipeline)

            # Store in GeoJSON format
            inspectionDate_geoJson = {"type": "FeatureCollection", "features": []}
            inspectionDateDefect_geoJson = {"type": "FeatureCollection", "features": []}
            inspectionDateNonDefect_geoJson = {"type": "FeatureCollection", "features": []}
            
            # Retrieve data from mongodb output
            for image in list(inspectionDate_data):
                # Condition to check if image has any associated defects
                defect_Condition = "imageDefects" in image
                # Write into Feature
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [image["longitude"], image["latitude"]]
                    },
                    "properties": {
                        "Type": image["imageDefects"]["outputLabel"] if defect_Condition else "NULL",
                        "Severity": image["imageDefects"]["severity"] if defect_Condition else "NULL",
                        "Confidence": image["imageDefects"]["confidence"] if defect_Condition else "NULL",
                        "ImageID": image["imageID"],
                        "OImagePath": image["imagePath"],
                        "BatchID": image["imageBatchDetails"]["batchID"],
                        "DateTime": image["datetime"],
                        "Road" : image["road"],
                        "Town": image["town"],
                        "RoadType": image["roadType"],
                        "Status": image["batchDetails"]["status"],
                        "BatchStartProcessing": image["batchDetails"]['batchStartProcessing'],
                        "BatchFinishProcessing": image["batchDetails"]['batchFinishProcessing'],
                        "DefectID": image["imageDefects"]["defectID"] if defect_Condition else "NULL"
                        }
                    }
                # Check if Defect/Non-Defect
                if defect_Condition:
                    # Defect
                    inspectionDateDefect_geoJson["features"].append(feature)
                else:
                    # Non Defect
                    inspectionDateNonDefect_geoJson["features"].append(feature)

                inspectionDate_geoJson["features"].append(feature)

            # Check if Specific Inspection Date directory exists, if it does, remove it
            if os.path.exists(inspectionDateData_path + f"/{inspection_date}"):
                shutil.rmtree(inspectionDateData_path + f"/{inspection_date}")
            # Remake Inspection Date directory
            os.mkdir(inspectionDateData_path + f"/{inspection_date}")

            # Save to geojson file
            save_geoJson_file(inspectionDate_geoJson, inspectionDateData_path + f"/{inspection_date}", inspection_date)
            try:
                save_geoJson_file(inspectionDateDefect_geoJson, inspectionDateData_path + f"/{inspection_date}", f"{inspection_date}_Defect")
            except Exception as e:
                # No Defects for that Inspection Date
                e
            try:
                save_geoJson_file(inspectionDateNonDefect_geoJson, inspectionDateData_path + f"/{inspection_date}", f"{inspection_date}_NonDefect")
            except Exception as e:
                # No Defects for that Inspection Date
                e

        return unique_dates_list
    except Exception as e:
        print("Error: ", e)
        return None