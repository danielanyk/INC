from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import os
import pandas as pd
import requests
import supervision as sv
import cv2
import imageio
import numpy as np
import subprocess
import time
import datetime
import geopandas as gpd
import gpxpy
from shapely.geometry import Point, Polygon
import shutil
import re
import sys
import json
from apps.home.config import ConfigData
from apps.home.address import Finder
import apps.home.state as state
from apps.home.report import get_reports, generate_report, get_bbox
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from apps.home.Tools.gv2f import extract_frames_with_metadata
app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/FYP"
mongo = PyMongo(app)
# db = mongo.db

# Create New Batch
def newBatch(path, totalframes, user_id, db):

    latest_batch = db.batch.find().sort('batchID', -1).limit(1)
    latest_batch_list = list(latest_batch)
    try:
        latest_batch_id = latest_batch_list[0]['batchID']
    except:
        latest_batch_id = 1

    new_batch_id = (latest_batch_id + 1) if latest_batch != 0 else 1
    
    # Get the current time

def new_batch(path, totalframes, user_id, db):
    # Fetch the latest batch ID safely
    latest_batch = list(db.batch.find().sort('batchID', -1).limit(1))
    new_batch_id = latest_batch[0]['batchID'] + 1 if latest_batch else 1
    current_time = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")

    try:
        db.batch.insert_one({
            "batchID": new_batch_id,
            "batchPath": path,
            "userID": user_id,
            "batchStartProcessing": current_time,
            "batchFinishProcessing": "-",
            "status": "pre-processing",
            "totalFrames": totalframes,
            "framesProcessed": 0
        })

    except Exception as e:
        return {'error': str(e)}, 500
    return {'message': 'Batch created successfully', 'batch_id': new_batch_id}

# Video Splitting Functions
def run_command(*args):
    try:
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ, text=True)
        stdout, stderr = process.communicate(timeout=180)  # Set timeout to 180 seconds
        return stdout, stderr
    except subprocess.TimeoutExpired:
        process.terminate()
        stdout, stderr = process.communicate()
        print("Process Terminated due to Timeout (Likely Lack of Geodata)")
        return stdout, False
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr
    finally:
        process.terminate()

def get_town(frame_data, lat, lon, output_dir, db):
    if frame_data is None:
        frame_data = pd.DataFrame()
        frame_data["lat"] = [lat]
        frame_data["lon"] = [lon]
    
    map = gpd.read_file(
        "apps/home/mygeodata/MasterPlan2019PlanningAreaBoundaryNoSea-polygon.shp"
    )
    polygon = map.to_crs(epsg=4326)
    frame_data["Town"] = "Not Specified"
    frame_data["roadType"] = "Asphalt"
    frame_data["road"] = "Not Specified"

    # replace the coordinates below with LONGITUDE and LATITUDE
    try:
        image_id = db.image.find_one(sort=[("imageID", -1)])["imageID"] 
    except:
        image_id = 0
    for i in range(len(frame_data["lon"])):
        # image_ID
        image_id = image_id + 1
        frame_data.at[i, "imageID"] = int(image_id)
        # file_name update
        frame_data.at[i, 'file_name'] = os.path.join(output_dir, frame_data.at[i, 'file_name'])

        # Town information
        point = Point(frame_data["lon"][i], frame_data["lat"][i])
        district = point.within(polygon["geometry"])
        district_name = polygon.loc[district[district == True].index]["PLN_AREA_N"].values[0]
        frame_data.at[i, "town"] = district_name

        #Road Information 
        finder = Finder("Roads.csv")        
        lat, lon, road, roadType = finder.find_closest_road(frame_data.at[i, "lat"], frame_data.at[i, "lon"])
        frame_data.at[i, "road"] = road
        frame_data.at[i, "roadType"] = roadType


    frame_data["datetime"] = datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")
    new_order = ["imageID", "file_name", "lat", "lon", "town", "road", "roadType", "datetime"]
    rename = {"file_name" : "imagePath", "lat": "latitude", "lon": "longitude"}
    frame_data['imageID'] = frame_data['imageID'].astype(int)

    frame_data = frame_data[new_order]
    frame_data = frame_data.rename(columns=rename)
    
    return frame_data

# def process_video_frames(video_path, db, batchfolder=None):
#     print(video_path)

#     exiftool = os.path.join("apps/home/Tools", "exiftool.exe")
#     ffmpeg = os.path.join("apps/home/Tools", "ffmpeg.exe")
#     gv2gf_v2 = os.path.join("apps/home/Tools", "gv2gf_v2.py")
    
#     try:
#         assert os.path.exists(exiftool)
#         assert os.path.exists(ffmpeg)
#         assert os.path.exists(gv2gf_v2)
    
#     except AssertionError:
#         print("Error: 1/More of the Tools not found")
#         return
    
#     video_name = os.path.splitext(os.path.basename(video_path))[0]

#     if batchfolder == None:
#         output_directory = os.path.join("Batches", video_name)
#     else: 
#         output_directory = os.path.join("Batches", batchfolder, video_name)
    
#     print(os.path.abspath(output_directory), "Absolute Path to Split Video Location")

#     if os.path.exists(output_directory):
#         # Remove directory and all its contents - if not, it doesn't work...
#         shutil.rmtree(output_directory)
    
#     os.makedirs(output_directory, exist_ok=True)

#     stdout, stderr = run_command("py", gv2gf_v2, "-t", "timegps", "-e", exiftool, "-f", ffmpeg, "-r", "1", video_path, output_directory) #
#     print("\n\n\n")
#     print(stdout, stderr)
#     print("\n\n\n")
#     if stderr==False:
#         print("video failed to split")
#         return False
    
#     print(stdout, stderr)            
#     print(f"Finished Generating Frames for {video_path} - {output_directory}")



#     # # Locate and read the CSV file
#     csv_name = video_name + ".csv"
#     csv_loc = os.path.join(output_directory, csv_name)
#     if not os.path.exists(csv_loc):
#         print(f"CSV file {csv_loc} was not created. Possibly no GPS data in video.")
#     frame_info = pd.read_csv(csv_loc)


#     # Remove the CSV file (sensitive information)
#     os.remove(os.path.join(csv_loc))

#     new_path = os.path.abspath(output_directory)

#     frame_info = get_town(frame_info, None, None, output_dir=new_path, db=db)
#     frame_info = frame_info.drop(frame_info.index[-1])

#     db.image.insert_many(frame_info.to_dict(orient="records"))

#     columns_to_drop = ["imagePath", "latitude", "longitude", "town", "road", "roadType", "datetime"]
#     frame_info = frame_info.drop(columns=columns_to_drop)
#     max_batch_id = list(db.batch.find().sort('batchID', -1).limit(1))[0]['batchID']
    
#     frame_info['batchID'] = max_batch_id
#     frame_info['batchID'] = frame_info['batchID'].astype(int)

#     db.batchImage.insert_many(frame_info.to_dict(orient="records"))
#     return "Success"

# Assuming run_command is already defined elsewhere in your codebase
# def process_video_frames(video_path, db, batchfolder=None):
#     """
#     Extracts frames from a video using gv2f.py (no GPS data),
#     inserts placeholder geodata records into MongoDB so that frames
#     can be queried, and links them to the current batch.
#     """
#     print(f"Processing video: {video_path}")

#     ffmpeg = os.path.join("apps/home/Tools", "ffmpeg.exe")
#     gv2f_py = os.path.join("apps/home/Tools", "gv2f.py")

#     # Verify tools exist
#     if not os.path.exists(ffmpeg) or not os.path.exists(gv2f_py):
#         print("Error: FFmpeg or gv2f.py not found")
#         return False

#     # Determine output directory
#     video_name = os.path.splitext(os.path.basename(video_path))[0]
#     if batchfolder:
#         output_directory = os.path.join("Batches", batchfolder, video_name)
#     else:
#         output_directory = os.path.join("Batches", video_name)

#     # Absolute path to batch folder
#     abs_output = os.path.abspath(output_directory)
#     print("Output directory:", abs_output)

#     # Clean/create output directory
#     if os.path.exists(abs_output):
#         shutil.rmtree(abs_output)
#     os.makedirs(abs_output, exist_ok=True)

#     # Run frame extraction
#     print("Running frame extraction script...")
#     stdout, stderr = run_command(
#         "py", gv2f_py,
#         "-f", ffmpeg,
#         "-r", "1",
#         video_path,
#         abs_output
#     )
#     print("STDOUT:", stdout)
#     print("STDERR:", stderr)

#     # Check for errors
#     if stderr:
#         print("Error during frame extraction; aborting.")
#         return False

#     # List extracted frames
#     frames = sorted(
#         [f for f in os.listdir(abs_output) if f.lower().endswith((".jpg", ".png"))]
#     )
#     if not frames:
#         print("No frames generated.")
#         return False

#     print(f"Extracted {len(frames)} frames to {abs_output}")

#     # Determine next batchID
#     batch_doc = db.batch.find_one(sort=[('batchID', -1)])
#     if not batch_doc:
#         print("No batch found in DB. Cannot link images to batch.")
#         return False
#     batch_id = int(batch_doc['batchID'])

#     # Determine next imageID
#     img_doc = db.image.find_one(sort=[('imageID', -1)])
#     next_img_id = int(img_doc['imageID']) + 1 if img_doc and 'imageID' in img_doc else 1

#     # Placeholder geodata (center of Singapore)
#     DEFAULT_LAT = 1.3521
#     DEFAULT_LON = 103.8198
#     DEFAULT_TOWN = "Unknown"
#     DEFAULT_ROAD = "Unknown"
#     DEFAULT_ROADTYPE = "Unknown"

#     image_records = []
#     batch_records = []
#     for fname in frames:
#         # absolute path for imagePath
#         abs_path = os.path.join(abs_output, fname)
#         record = {
#             'imageID': next_img_id,
#             'imagePath': abs_path,
#             'latitude': DEFAULT_LAT,
#             'longitude': DEFAULT_LON,
#             'town': DEFAULT_TOWN,
#             'road': DEFAULT_ROAD,
#             'roadType': DEFAULT_ROADTYPE,
#             'datetime': os.path.splitext(fname)[0]
#         }
#         image_records.append(record)
#         batch_records.append({'batchID': batch_id, 'imageID': next_img_id})
#         next_img_id += 1

#     # Insert image docs
#     try:
#         db.image.insert_many(image_records)
#         print(f"Inserted {len(image_records)} image records into db.image")
#     except Exception as e:
#         print("Error inserting image records:", e)
#         return False

#     # Insert batch-image links
#     try:
#         db.batchImage.insert_many(batch_records)
#         print(f"Inserted {len(batch_records)} records into db.batchImage")
#     except Exception as e:
#         print("Error inserting batchImage records:", e)
#         return False

#     return "Success"

def process_video_frames(video_path: str, db, batchfolder: str = None):
    """
    Extract frames and metadata from a video, enrich with location info, insert into MongoDB.
    """
    print(f"Processing video: {video_path}")

    # 1. Prepare output path and tools
    ffmpeg = os.path.join("apps/home/Tools", "ffmpeg.exe")
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    out_dir = os.path.abspath(os.path.join("Batches", batchfolder or "", video_name))
    
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # 2. Frame extraction + GPS/time metadata
    meta, frames = extract_frames_with_metadata(ffmpeg, video_path, out_dir, frame_rate=1)
    if not frames:
        print("No frames generated.")
        return False

    # 3. Prepare metadata into a DataFrame
    frame_info = pd.DataFrame({
        "file_name": frames,
        "lat": [meta['latitude']] * len(frames),
        "lon": [meta['longitude']] * len(frames)
    })

    # 4. Add geolocation details using get_town
    frame_info = get_town(frame_info, None, None, output_dir=out_dir, db=db)
    if len(frame_info) > 1:
        frame_info = frame_info.drop(frame_info.index[-1])  # drop last row like before

    # 5. Insert into db.image
    db.image.insert_many(frame_info.to_dict(orient="records"))

    # 6. Prepare for db.batchImage insertion
    frame_info = frame_info.drop(columns=["imagePath", "latitude", "longitude", "town", "road", "roadType", "datetime"])
    max_batch = db.batch.find_one(sort=[('batchID', -1)])
    if not max_batch:
        print("No batch found in DB.")
        return False

    frame_info["batchID"] = int(max_batch["batchID"])
    db.batchImage.insert_many(frame_info.to_dict(orient="records"))

    print(f"Inserted {len(frames)} frames with location info into MongoDB.")
    return "Success"


def process_images(path, lat, lon, db):
    if lat or lon is None:
        lat = 1.3521
        lon = 103.8198

    frame_info = get_town(None, lat, lon, db=db)

    columns_to_drop = ["imagePath", "latitude", "longitude", "town", "road", "roadType", "datetime"]
    frame_info = frame_info.drop(columns=columns_to_drop)

    max_batch_id = list(db.batch.find().sort('batchID', -1).limit(1))[0]['batchID']
    frame_info['batchID'] = max_batch_id
    frame_info['batchID'] = frame_info['batchID'].astype(int)

    db.batchImage.insert_one(frame_info.to_dict(orient="records"))
    return "Success"
    #make a copy of the image and move to directory

def is_image_or_video(filename):
    image_video_extensions = [".jpg", ".jpeg", ".png", ".mp4"]
    _, ext = os.path.splitext(filename)
    return ext.lower() in image_video_extensions

def split_process(path, lat, lon, db, bid=None):
    if bid is not None:
        db.batch.update_one({"batchID": bid}, {"$set": {"status": "Splitting"}})
    
    # Single Video
    if path.endswith(".mp4"):
        process_video_frames(path, db)

    # Single Image
    elif path.endswith((".jpg", ".jpeg", ".png")):
        os.makedirs(os.path.join("Batches", "Individual_Images"), exist_ok=True)
        process_images(path, lat, lon, db)
        shutil.copy(path, os.path.join("Batches", "Individual Images"))

    # Folder
    else:
        batchfolder = os.path.splitext(os.path.basename(path))[0]
        os.makedirs(os.path.join("Batches", batchfolder), exist_ok=True)
        files = [
            file
            for file in os.listdir(path)
            if os.path.isfile(os.path.join(path, file)) and is_image_or_video(file)
        ]
    
        if not files:
            return {"result": "No files found"}, 404
        
        for filename in files:
            filepath = os.path.join(path, filename)
            if filename.endswith(".mp4"):
                try:
                    process_video_frames(video_path=filepath,db=db, batchfolder=batchfolder)
                except:
                    print(f"Video {filename} was unable to be split")
                    continue
            elif filename.endswith((".jpg", ".jpeg", ".png")):
                continue
                
# Image Processing Functions
def get_list_of_images(db):
    try:
        # Get the latest batch_id
        latest_batch = db.batchImage.find().sort('batchID', -1).limit(1) 

        latest_batch_list = list(latest_batch)
        latest_batch_id = latest_batch_list[0]['batchID'] if latest_batch_list else 1

        if latest_batch_id is None:
            return jsonify([]), 200
        
        # Perform the aggregation to retrieve image details
        pipeline = [
            {'$match': {'batchID': latest_batch_id}},
            {
                '$lookup': {
                    'from': 'image',
                    'localField': 'imageID',
                    'foreignField': 'imageID',
                    'as': 'imageDetails'
                }
            },
            {'$unwind': '$imageDetails'},
            {'$replaceRoot': {'newRoot': '$imageDetails'}},
            { '$project': { '_id': 0, 'imagePath': 1, 'imageID' : 1} }
        ]
        
        # images = db.batchImage.aggregate(pipeline)
        images = list(db.batchImage.aggregate(pipeline))

        return images
    except Exception as e:
        return f'Error: DBMS Exception: {e}', 500

# Inference Functions
def send_prediction_request(image_path, predict_url):
    try:
        input_data = {"image_path": image_path} 
        response = requests.post(predict_url, json=input_data)
    except Exception as e:
        print(f"Error: {e}")
        print("Something wrong with the post request")
        return None

    if response.status_code == 200:
        response_data = response.json()
        # print(response_data)

        if predict_url == "http://localhost:5005/predictSeverity":
            severityLevel = response_data["severity"]
            return severityLevel # returns e.g. 1
        else:
            # result = response_data["result"]
            class_id = response_data["class_id"]
            output_lbl = response_data["output_lbl"]
            xyxy = response_data["xyxy"]
            confidence = response_data["confidence"]

        return output_lbl, xyxy, confidence, class_id  
    else:
        print(f"Prediction Error with {image_path} and {predict_url} ")
        # print("Error:", response.status_code, response.text)
        return False, False, False, False

def crop_image(image_path, bbox, identifier = None):
    image = cv2.imread(image_path)
    # bbox coordinates must be integer
    x_min, y_min, x_max, y_max = map(int, bbox)
    # Crop frame to defect region
    cropped_image = image[y_min:y_max, x_min:x_max]

    # Extract original file name without file extension
    original_image_name, extension = os.path.splitext(os.path.basename(image_path))
    # Set cropped image file name
    if identifier is not None:
        cropped_image_name = f"{original_image_name}_cropped_{identifier}{extension}"
    else:
        cropped_image_name = f"{original_image_name}_cropped{extension}"
    # Directory to store cropped image [File path to be changed]
    AL_dir = r".\active_learning\unedited" 
    # Create cropped image file path
    cropped_image_path = os.path.join(AL_dir, cropped_image_name)

    # Save cropped image to saving directory
    try:
        cv2.imwrite(cropped_image_path, cropped_image)
        print(f"{image_path} has been cropped, saved to {cropped_image_path}")
    except Exception as e:
        print(e)
        print("Unable to save cropped image")

    return cropped_image_path

# [Team HotPink][Code]
# Rename cropped image file path to be with defectID for QGIS & MongoDB connection
def rename_croppedImagePath(cropped_image_path, defectID, identifier = None):
    # Extract cropped image file name without file extension
    cropped_image_name, extension = os.path.splitext(os.path.basename(cropped_image_path))
    if identifier is not None:
        substring = f'cropped_{identifier}'
    else: 
        substring = 'cropped'
    # Find start index of 'cropped'
    start_index = cropped_image_name.find(substring)
    # Remove substring using slicing
    if start_index != -1:
        new_name = cropped_image_name[:start_index] + cropped_image_name[start_index + len(substring):]
    else:
        raise ValueError(f"Substring '{substring}' not found in '{cropped_image_name}'.")
    # Add defectID in new image name
    new_cropped_image_name = f"{new_name}{defectID}{extension}"

    # Directory to store cropped image [File path to be changed]
    AL_dir = r'.\active_learning\unedited'
    # Construct new file path
    new_cropped_image_file_path = os.path.join(AL_dir, new_cropped_image_name)
    # Rename the file
    try:
        os.rename(cropped_image_path, new_cropped_image_file_path)
    except Exception as e:
        print(e)
        print("Unable to rename cropped image file path")

def make_inferences(db,tog,bid=None, toggle_confidence=False, inspectionDate=None):
    predict_url = [
    "http://localhost:5001/predictRaveling",
    "http://localhost:5002/predict17Defects",
    "http://localhost:5003/predictKerb",
    "http://localhost:5004/predictPaint",
    "http://localhost:5009/api/predict"
    ]
    urls=[]
    for i in range(len(tog)):
        if tog[i]==True:
            urls.append(predict_url[i]) 
        else:
            urls.append('')
    try: 
        images = get_list_of_images(db=db)
    except Exception as e:
        return f'Error: DBMS Exception: {e}', 500      
    image_df = pd.DataFrame(images)
    if bid==None:
        latest_batch = db.batch.find().sort('batchID', -1).limit(1)
        print("latest_batch",latest_batch)
        latest_batch_list = list(latest_batch)
        bid = latest_batch_list[0]['batchID'] + 1 if latest_batch_list else 1
    else:
        db.batch.update_one({"batchID": bid}, {"$set": {"status": "Inferencing"}})
    print(image_df['imageID'])
    print(urls)
    for i in range(len(image_df['imagePath'])):
        if state.stop_flag:  # ✅ Read the shared value here
            print("Stopping early")
            break
        frame = image_df['imagePath'][i]
        for j in range(len(urls)):
            if urls[j]=='':
                continue
            print("\n","Printing urls","\n",urls,tog,frame)
            output_lbl, xyxy, confidence, class_id = send_prediction_request(frame, urls[j])
            if output_lbl==False:
                continue
            if len(output_lbl) == 0: 
                continue
            
            if urls[j]!="http://localhost:5003/predictKerb" and urls[j]!="": # Do not run severity engine on kerb defects
                severity_predict_url = "http://localhost:5005/predictSeverity"
                severity_array = [] # Array to store severity labels
                croppedImage_path_array = [] # Array to store croppedImage_path_array
                # Loop through multiple detected defects individually in a frame
                if len(confidence) > 1: # More than one detected defect in a frame
                    for k in range(len(confidence)):
                        xyxy_current = xyxy[k]
                        croppedImage_path = crop_image(frame, xyxy_current, k) # Crop image
                        severity = send_prediction_request(croppedImage_path, severity_predict_url) # Run severity engine
                        severity_array.append(severity)
                        croppedImage_path_array.append(croppedImage_path)
                else: # Singular defect detected in a frame
                    xyxy_current = xyxy[0]
                    croppedImage_path = crop_image(frame, xyxy_current) # Crop image
                    severity = send_prediction_request(croppedImage_path, severity_predict_url) # Run severity engine
                    severity_array.append(severity)
                    croppedImage_path_array.append(croppedImage_path)

                detection_import(image_df, frame, xyxy, confidence, output_lbl, class_id, db, j+1, severity_array, croppedImage_path_array)
            else:
                detection_import(image_df, frame, xyxy, confidence, output_lbl, class_id, db, j+1)

        if db.defect.find_one({"imageID": int(image_df["imageID"][i])}): 
            print(int(image_df["imageID"][i]))

            apply_to_image(db, inspectionDate=inspectionDate, image_id=int(image_df["imageID"][i]), toggle_confidence=toggle_confidence)

        # Update the framesProcessed field in the batch collection
        if int(db.batch.find_one({"batchID": bid})['framesProcessed']) < int(db.batch.find_one({"batchID": bid})['totalFrames']):
            db.batch.update_one({"batchID": bid}, {"$inc": {"framesProcessed": 1}})

# Importing Defects into DB
def detection_import(image_df, frame, xyxy, confidence, output_lbl, output_id, db, engine_number, severityLevel = None, croppedImgPath_array = None):
    image_id = image_df[image_df['imagePath']==frame]['imageID'].values[0]  
    xyxy = eval(f"{xyxy}")

    if len(confidence)>1:
        for i in range(len(confidence)):            
            current_max = list(db.defect.find().sort('defectID', -1).limit(1))
            current_max = current_max[0]['defectID'] if current_max else None
            defect_id = current_max + 1 if current_max else 1
            current_confidence = confidence[i]
            current_output_lbl = output_lbl[i]
            current_output_id = output_id[i]
            xyxy_current = xyxy[i]

            if croppedImgPath_array is not None:
                croppedImgPath = croppedImgPath_array[i]
            print(engine_number)
            if engine_number == 1:
                severity = severityLevel[i] # [Team HotPink][Code]
                # Rename old cropped image file path to include defectID
                rename_croppedImagePath(croppedImgPath, defect_id, i) # [Team HotPink][Code]
                output_output_id = 17

            elif engine_number == 2:
                severity = severityLevel[i] # [Team HotPink][Code]
                # Rename old cropped image file path to include defectID
                rename_croppedImagePath(croppedImgPath, defect_id, i) # [Team HotPink][Code]
                output_output_id = current_output_id + 1

            elif engine_number == 3: # [Team HotPink][Comment] Kerb Engine
                severity = int(str(current_output_lbl).strip('Faded Kerb')[1])
                current_output_lbl = current_output_lbl.split(" ")[0] + " " + current_output_lbl.split(" ")[1] + " " + current_output_lbl.split(" ")[3]
                output_output_id = 18

            elif engine_number == 4:
                severity = severityLevel[i]
                # Rename old cropped image file path to include defectID
                rename_croppedImagePath(croppedImgPath, defect_id, i) # [Team HotPink][Code]
                output_output_id = 19
            
            elif engine_number == 5:
                severity = severityLevel[i]
                # Rename old cropped image file path to include defectID
                rename_croppedImagePath(croppedImgPath, defect_id, i) # [Team Teal][Code]
                output_output_id = 20

            db.defect.insert_one({
                "defectID" : defect_id,
                "imageID": int(image_id),
                "outputLabel": current_output_lbl, 
                "outputID": output_output_id,
                "confidence": current_confidence,
                "bbox": str(xyxy_current),
                "severity": severity
                })
    else: 
        current_max = list(db.defect.find().sort('defectID', -1).limit(1))
        current_max = current_max[0]['defectID'] if current_max else None
        defect_id = current_max + 1 if current_max else 1
        xyxy_single = xyxy[0]
        xyxy_single = str(xyxy_single)
        output_lbl = output_lbl[0]
        confidence = confidence[0]

        if croppedImgPath_array is not None:
            croppedImgPath = croppedImgPath_array[0]

        if engine_number == 1:
            severity = severityLevel[0] # [Team HotPink][Code]
            # Rename old cropped image file path to include defectID
            rename_croppedImagePath(croppedImgPath, defect_id) # [Team HotPink][Code]
            output_output_id = 17

        elif engine_number == 2:
            severity = severityLevel[0] # [Team HotPink][Code]
            # Rename old cropped image file path to include defectID
            rename_croppedImagePath(croppedImgPath, defect_id) # [Team HotPink][Code]
            output_output_id = output_id[0] + 1
        
        elif engine_number == 3:
            severity = int(str(output_lbl).strip('Faded Kerb')[1])
            output_lbl = output_lbl.split(" ")[0] + " " + output_lbl.split(" ")[1] + " " + output_lbl.split(" ")[3]
            output_output_id = 18
        
        elif engine_number == 4:
            severity = severityLevel[0]
            output_output_id = 19
        
        elif engine_number == 5:
            severity = severityLevel[0]
                # Rename old cropped image file path to include defectID
                # rename_croppedImagePath(croppedImgPath, defect_id, i) # [Team Teal][Code]
            output_output_id = 20
        
        db.defect.insert_one({
            "defectID" : defect_id,
            "imageID": int(image_id),
            "outputLabel": str(output_lbl),
            "outputID": output_output_id,
            "confidence": confidence,
            "bbox": str(xyxy_single),
            "severity": severity
        })

def get_class_id(defect):
    preprocessed_label = defect.strip().lower()
    # Retrieve the class ID from the dictionary
    # change defect_classes to be read from db
    class_id = defect_classes.get(preprocessed_label, None)  # Return None if the label is not found

    if class_id is None:
        # change to add new defect to newly made defect_class collection and reannotate accordingly
        # Check if preprocessed_label is already in labels.txt
        with open('labels.txt', 'r') as file:
            labels = file.read().splitlines()

        if preprocessed_label not in labels:
            # Add defect to labels.txt
            with open('labels.txt', 'a') as file:
                file.write(f"\n{preprocessed_label}")
                
        # Add defect to defect_classes dictionary, for now (to change to db when implemented)
        class_id = len(defect_classes) + 1
        print(f'Added new defect label: {preprocessed_label} with class_id: {class_id}')
        # raise ValueError(f"Unknown defect label: {preprocessed_label}")
    return class_id

# Applying Defects to singular Images
def apply_to_image(db, inspectionDate=None, bid=None, image_id=None, toggle_confidence=False, reannotating=False):

    color_map = {
        'Alligator Crack': (255, 69, 0),          # Red-Orange
        'Arrow': (0, 255, 127),                   # Spring Green
        'Blockcrack': (0, 191, 255),              # Deep Sky Blue
        'Damaged Base Crack': (255, 215, 0),      # Gold
        'Localise Surface Defect': (238, 130, 238),# Violet
        'Multicrack': (0, 255, 255),              # Cyan
        'Parallel Lines': (255, 20, 147),         # Deep Pink
        'Peel Off With Cracks': (154, 205, 50),   # Yellow-Green
        'Peeling Off Premix': (144, 238, 144),    # Light Green
        'Pothole With Crack': (148, 0, 211),      # Dark Violet
        'Rigid Pavement Crack': (0, 206, 209),    # Dark Turquoise
        'Single Crack': (255, 255, 240),          # Ivory
        'Transverse Crack': (70, 130, 180),       # Steel Blue
        'Wearing Course Peeling Off': (255, 140, 0), # Dark Orange
        'White Lane': (240, 255, 255),            # Azure
        'Yellow Lane': (255, 255, 0),             # Yellow (unchanged)
        'Raveling': (169, 169, 169),              # Dark Gray
        'Faded Kerb': (135, 206, 250),            # Light Sky Blue
        'Paint Spillage': (123, 104, 238),        # Medium Slate Blue
        'Drainage': (255, 255, 0)
    }

    pipeline = [
        {
            "$lookup": {
                "from": "defect",
                "localField": "imageID",
                "foreignField": "imageID",
                "as": "defects"
            } 
        },
        {
            "$unwind": {
                "path": "$defects",
                "preserveNullAndEmptyArrays": False
            }
        },
        {
            "$match": {
                "imageID": image_id
            }
        },
        {
            "$sort": {
                "defects.defectID": 1
            }
        },
        {
            "$group": {
                "_id": "$imageID",
                "imagePath": {"$first": "$imagePath"},
                "defects": {"$push": "$defects.outputLabel"},
                "bbox": {"$push": "$defects.bbox"},
                "confidence": {"$push": "$defects.confidence"},
                "outputID": {"$push": "$defects.outputID"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "imagePath": 1,
                "imageID": "$_id",
                "defects": 1,
                "outputID": 1,
                "bbox": 1,
                "confidence": 1
            }
        }
    ]

    defected_image = list(db.image.aggregate(pipeline))

    # class_id = np.array([defect_id for defect_id in defected_image[0]['defects']])
    bbox = np.array([eval(x) for x in defected_image[0]['bbox']])
    confidence = np.array(defected_image[0]['confidence'])
    output_lbl = list(defected_image[0]['defects'])
    
    copy_output_lbl = np.copy(output_lbl)
    for j in range(len(copy_output_lbl)):
        if "Faded Kerb" in copy_output_lbl[j]:
            copy_output_lbl[j] = "Faded Kerb" 
    class_id = []
    for i in range(len(copy_output_lbl)):
        try:
            defectid = defect_classes[copy_output_lbl[i]]
            class_id.append(defectid)
        except:
            class_id.append(20)
    class_id = np.array(class_id)

    
    if toggle_confidence == True: 
        legend = {label: color_map[label] for label in unique_labels}
        for j in range(len(output_lbl)):
            output_lbl[j] = f"{str(output_lbl[j])} {confidence[j]:.4f}"
            
    output_lbl = np.array(output_lbl)

    detections = sv.Detections(xyxy= bbox, confidence=confidence, class_id=class_id)
    image_path = defected_image[0]['imagePath']
    
    box_annotator = sv.BoxAnnotator(color = sv.Color.RED, thickness=10, text_scale=3, text_color=sv.Color.WHITE, text_thickness=10)
    annotated_frame = box_annotator.annotate(
        scene=cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB),
        detections=detections,
        labels=output_lbl
    )

    defect_img = image_path.replace(".jpg", "_defect.jpg")
    imageio.imwrite(defect_img, annotated_frame)
    
    # Annotation Using Legends
    try:
        # Load and convert the image
        image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)

        copy_output_lbl = np.copy(output_lbl)
        for j in range(len(copy_output_lbl)):
            if "Faded Kerb" in copy_output_lbl[j]:
                copy_output_lbl[j] = "Faded Kerb" 
    
        unique_labels = set(copy_output_lbl)
        if toggle_confidence==False:
            legend = {label: color_map[label] for label in unique_labels}

        for i in range(len(detections)):
            x1, y1, x2, y2 = map(int, bbox[i]) 
            color = legend[copy_output_lbl[i]]
            cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness = 8)  

        image_height, image_width = image.shape[:2]
        legend_height = 40 + len(legend) * 90
        legend_canvas = np.ones((legend_height, image_width, 3), dtype=np.uint8) * 255  

        font_scale = 3
        thickness = 6

        for idx, (label, color) in enumerate(legend.items()):
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            text_width, text_height = text_size[0]

            rect_width = 30  
            rect_height = text_height + 10  
            
            top_left = (20, 20 + idx * (rect_height + 20))  
            bottom_right = (20 + rect_width, 20 + idx * (rect_height + 20) + rect_height)
            cv2.rectangle(legend_canvas, top_left, bottom_right, color, -1)
            
            text_x = bottom_right[0] + 10
            text_y = top_left[1] + rect_height - 5
            
            cv2.putText(legend_canvas, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)

        combined_image = np.vstack((image, legend_canvas))
        plt.figure(figsize = (30,20))
        plt.imshow(combined_image)
        plt.axis('off')  
        legend_save_path = image_path.replace(".jpg", "_legend_defect.jpg")
        plt.savefig(legend_save_path, bbox_inches='tight', pad_inches=0, format='jpg')
        plt.close()
    except:
        print('Legend Image Failed to Generate')

    try:
    # Load the original image
        image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)

        copy_output_lbl = np.copy(output_lbl)
        for j in range(len(copy_output_lbl)):
            if "Faded Kerb" in copy_output_lbl[j]:
                copy_output_lbl[j] = "Faded Kerb" 

        unique_labels = set(copy_output_lbl)
        legend = {label: color_map[label] for label in unique_labels}

        # Generate separate images for each defect type
        for defect_type in unique_labels:
            # Create a copy of the original image
            defect_image = image.copy()

            # Annotate only the bounding boxes for the current defect type
            for i in range(len(detections)):
                if copy_output_lbl[i] == defect_type:
                    x1, y1, x2, y2 = map(int, bbox[i])
                    color = legend[defect_type]
                    cv2.rectangle(defect_image, (x1, y1), (x2, y2), color, thickness=8)

            # Save the annotated image for the current defect type
            defect_image_path = image_path.replace(".jpg", f"_{defect_type.replace(' ', '_')}_defect.jpg")
            cv2.imwrite(defect_image_path, cv2.cvtColor(defect_image, cv2.COLOR_RGB2BGR))

            print(f"Generated defect image for {defect_type}: {defect_image_path}")

            # REPORT SECTION
            # push to report collection using imageID

            defect_classes = {
                '1': {"class": "bg-emerald-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Alligator Crack"},
                '2': {"class": "bg-yellow-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Arrow"},
                '3': {"class": "bg-green-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Block Crack"},
                '4': {"class": "bg-blue-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Damaged Base Crack"},
                '5': {"class": "bg-indigo-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Localise Surface Defect"},
                '6': {"class": "bg-purple-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Multi Crack"},
                '7': {"class": "bg-pink-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Parallel Lines"},
                '8': {"class": "bg-red-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Peel Off With Cracks"},
                '9': {"class": "bg-emerald-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Peeling Off Premix"},
                '10': {"class": "bg-green-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Pothole With Crack"},
                '11': {"class": "bg-blue-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Rigid Pavement Crack"},
                '12': {"class": "bg-indigo-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Single Crack"},
                '13': {"class": "bg-purple-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Transverse Crack"},
                '14': {"class": "bg-pink-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Wearing Course Peeling Off"},
                '15': {"class": "bg-white text-black text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "White Lane"},
                '16': {"class": "bg-amber-200 text-black text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Yellow Lane"},
                '17': {"class": "bg-green-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Raveling"},
                '18': {"class": "bg-blue-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Faded Kerb"},
                '19': {"class": "bg-indigo-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Paint Spillage"},
                '20': {"class": "bg-purple-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md", "text": "Drainage"},
                    }


            for key, value in defect_classes.items():
                if value["text"] == defect_type:
                    defectNumber=key

            max_report = db.report.find_one(sort=[("reportID", -1)])
            next_reportID = max_report["reportID"] + 1 if max_report else 1
            if not os.path.exists(os.path.abspath("Reports")):
                os.makedirs("Reports")
                print("Reports directory created")
            
            name = defect_image_path.split("\\")[-1].replace("_defect.jpg", ".pdf")
            batchfolder = image_path.split("\\")[-2]
            path = os.path.abspath("Reports")
            print("Path",path)
            reportPath = os.path.join(path, batchfolder, name)
            print("report path",reportPath)

            # if (not db.report.find_one({"imageID": image_id}) and reannotating) or not reannotating:
            db.report.insert_one(
                {
                    "reportID": int(next_reportID),
                    "imageID": int(defected_image[0]["imageID"]),
                    "inspectedBy": ConfigData.INSPECTOR_NAME, 
                    "inspectionDate": inspectionDate,
                    "inspectionType": ConfigData.INSPECTION_TYPE,
                    "generationTime": datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S"),
                    "reportPath": reportPath,
                    "defectNumber":defectNumber,
                    "tags": "",
                    "quantity": "",
                    "measurement": "",
                    "cause": "",
                    "recommendation": "",
                    "remarks": "",
                    "supervisor": "",
                    "via": "",
                    "acknowledgement": "",
                    "status":"unchecked"
                }
            )
            print(f"Entered MongoDB for {defect_type}: {defect_image_path}")
    except Exception as e:
        print(f"An error occurred while generating separate defect images: {e}")



    ## Generate Report PDF 
    print(int(defected_image[0]["imageID"]))
    data = get_reports(image_id=int(defected_image[0]["imageID"]))
    r_bbox = get_bbox(int(defected_image[0]["imageID"]))

    report_data = {
        "name": data[0]["Name"],
        "ins_type": data[0]["Inspection Type"],
        "ins_date": data[0]["Inspection Date"],
        "road_type": data[0]["RoadType"],
        "type": data[0]["Type"],
        "latitude": data[0]["Latitude"],
        "longitude": data[0]["Longitude"],
        "inspector": data[0]["Inspector"],
        "severity": data[0]["Severity"],
        "image": data[0]["Image"],
        "report_id": data[0]["ReportID"],
        "road": data[0]["Road"],
        "quantity": data[0]["Quantity"],
        "measurement": data[0]["Measurement"],
        "cause": data[0]["Cause"],
        "recommendation": data[0]["Recommendation"],
        "remarks": data[0]["Remarks"],
        "supervisor": data[0]["Supervisor"],
        "via": data[0]["Via"],
        "acknowledgement": data[0]["Acknowledgement"],
        "bbox": r_bbox,
    }
    selected_template = 1
    # generate_report(report_data, selected_template, 'download')

def saving_reportdata(db,data):
            defectimg = data.get('defectimg')
            defecttype = data.get('defecttype')
            imgpath = data.get('imgpath')
            inspected_by = data.get('inspectedBy')
            inspection_date = data.get('inspectionDate')
            defect_name = data.get('defectnumber')
            quantity = data.get('quantity')
            measurement = data.get('measurement')
            cause = data.get('cause')
            recommendation = data.get('recommendation')
            remarks = data.get('remarks')
            supervisor = data.get('supervisor')
            via = data.get('via')
            acknowledgement = data.get('acknowledgement')
            print('saving',imgpath,defecttype)
            defectRepeatedValue=data.get('defectRepeatedValue')
            pipeline = [
    # Join with image collection
    {
        "$lookup": {
            "from": "image",
            "localField": "imageID",
            "foreignField": "imageID",
            "as": "imageData"
        }
    },
    {"$unwind": "$imageData"},
    
    # Match imagePath == imgpath
    {
        "$match": {
            "imageData.imagePath": imgpath
        }
    },

    # Join with defect collection
    {
        "$lookup": {
            "from": "defect",
            "localField": "imageID",
            "foreignField": "imageID",
            "as": "defectData"
        }
    },
    {"$unwind": "$defectData"},

    # Match defect.outputLabel *contains* defecttype
    {
        "$match": {
            "defectData.outputLabel": {
                "$regex": defecttype,
                "$options": "i"  # Case-insensitive
            }
        }
    },

    # Ensure report.defectNumber == defect.outputID
    {
        "$match": {
            "$expr": {
                "$eq": [
                    {"$toString": "$defectData.outputID"},
                    "$defectNumber"
                ]
            }
        }
    },

    # Project only the desired field
    {
        "$project": {
            "_id": 0,
            "reportID": 1
        }
    }
]

            



            results = list(db.report.aggregate(pipeline))
  
            print("IMGAYYY",results)
            if len(results)>1:
                results=results[-1]
            else:
                results=results[0]
            
            update_data = {
                "$set": {
                    "inspectedBy": inspected_by,
                    "inspectionDate": inspection_date,
                    "inspectionType": ConfigData.INSPECTION_TYPE,
                    "generationTime": datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S"),
                    "tags": "",
                    "quantity": quantity,
                    "measurement": measurement,
                    "cause": cause,
                    "recommendation": recommendation,
                    "remarks": remarks,
                    "supervisor": supervisor,
                    "via": via,
                    "acknowledgement": acknowledgement,
                    "status":"checked"
                }
            }
            

            # Perform the update operation
            # results = list(db.report.aggregate(pipeline))
            if results:
                db.report.update_one({"reportID": results["reportID"]}, update_data)
            else:
                print("No matching report found")

            generate_new(db,results["reportID"],defecttype,defect_name,imgpath,defectRepeatedValue)
            
            return jsonify({"message": "success"})
            # print(f"Entered MongoDB for {defecttype}: {defectimg}")

def generate_new(db, report_id,defect_type,name,image,defectRepeatedValue):
    report = db.report.find_one({"reportID": report_id})
    if not report:
        raise ValueError(f"Report with reportID {report_id} not found.")

    image_id = report["imageID"]

    # Step 2: Fetch image by imageID
    image_doc = db.image.find_one({"imageID": image_id})
    if not image_doc:
        raise ValueError(f"Image with imageID {image_id} not found.")

    # Step 3: Fetch defect using imageID and partial match on outputLabel
    defect = db.defect.find_one({
        "imageID": image_id,
        "outputLabel": {"$regex": defect_type, "$options": "i"}
    })
    if not defect:
        raise ValueError(f"No defect found for imageID {image_id} with label containing '{defect_type}'.")

    # Assemble the final data using provided + fetched values
    report_data = {
        "name": name,  # provided
        "image": image,  # provided
        "report_id": report_id,  # provided
        "defect_type": defect_type,  # provided
        "ins_type": report["inspectionType"],
        "ins_date": report["inspectionDate"],
        "road_type": image_doc["roadType"],
        "latitude": image_doc["latitude"],
        "longitude": image_doc["longitude"],
        "inspector": report["inspectedBy"],
        "severity": defect["severity"],
        "road": image_doc["road"],
        "quantity": report.get("quantity", ""),
        "measurement": report.get("measurement", ""),
        "cause": report.get("cause", ""),
        "recommendation": report.get("recommendation", ""),
        "remarks": report.get("remarks", ""),
        "supervisor": report.get("supervisor", ""),
        "via": report.get("via", ""),
        "acknowledgement": report.get("acknowledgement", ""),
        "filtered_bbox": defect["bbox"],
        "defectRepeatedValue":defectRepeatedValue
    }

    generate_report(report_data, defect_type, "template1", 'download')

def changing_reportdata(db,data):

    defectimg = data.get('defectimg')
    defecttype = data.get('defecttype')
    imgpath = data.get('imgpath')
    inspected_by = data.get('inspectedBy')
    inspection_date = data.get('inspectionDate')
    defect_name = data.get('defectnumber')
    quantity = data.get('quantity')
    measurement = data.get('measurement')
    cause = data.get('cause')
    recommendation = data.get('recommendation')
    remarks = data.get('remarks')
    supervisor = data.get('supervisor')
    via = data.get('via')
    acknowledgement = data.get('acknowledgement')
    defectRepeatedValue=data.get('defectRepeatedValue')
    print('saving', imgpath, defecttype)

    pipeline = [
        {
            "$lookup": {
                "from": "image",
                "localField": "imageID",
                "foreignField": "imageID",
                "as": "imageData"
            }
        },
        {"$unwind": "$imageData"},
        {
            "$match": {
                "imageData.imagePath": imgpath
            }
        },
        {
            "$lookup": {
                "from": "defect",
                "localField": "imageID",
                "foreignField": "imageID",
                "as": "defectData"
            }
        },
        {"$unwind": "$defectData"},
        {
            "$match": {
                "defectData.outputLabel": {
                    "$regex": defecttype,
                    "$options": "i"
                }
            }
        },
        {
            "$match": {
                "$expr": {
                    "$eq": [
                        {"$toString": "$defectData.outputID"},
                        "$defectNumber"
                    ]
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "reportID": 1
            }
        }
    ]

    results = list(db.report.aggregate(pipeline))
    print("IMGAYYY", results)

    if not results:
        print("No matching report found")
        return jsonify({"message": "No matching report found"}), 404

    if len(results)>1:
                results=results[-1]
    else:
                results=results[0]
            
    # Dynamically create $set fields only when they have value
    dynamic_fields = {
        "inspectedBy": inspected_by,
        "inspectionDate": inspection_date,
        "inspectionType": ConfigData.INSPECTION_TYPE,
        "generationTime": datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S"),
        "tags": "",
        "quantity": quantity,
        "measurement": measurement,
        "cause": cause,
        "recommendation": recommendation,
        "remarks": remarks,
        "supervisor": supervisor,
        "via": via,
        "acknowledgement": acknowledgement,
        "status": "checked"
    }

    update_data = {"$set": {k: v for k, v in dynamic_fields.items() if v not in (None, "", [])}}

    db.report.update_one({"reportID": results["reportID"]}, update_data)
    generate_new(db,results["reportID"],defecttype,defect_name,imgpath,defectRepeatedValue)
    return jsonify({"message": "success"})



defect_classes = {
    "Alligator Crack": 1,
    "Arrow": 2,
    "Block Crack": 3,
    "Damaged Base Crack": 4,
    "Localised Surface Defect": 5,
    "Multi Crack": 6,
    "Parallel Lines": 7,
    "Peel Off With Cracks": 8,
    "Peeling Off Premix": 9,
    "Pothole With Crack": 10,
    "Rigid Pavement Crack": 11,
    "Single Crack": 12,
    "Transverse Crack": 13,
    "Wearing Course Peeling Off": 14,
    "White Lane": 15,
    "Yellow Lane": 16,
    "Raveling": 17,
    "Faded Kerb": 18,
    "Paint Spillage": 19,
    "Drainage": 20,
}


def pipeline(db, inspectionDate, path,tog, user_id = 1, lat = None, lon = None, totalframes = 300, toggle_confidence=False, bid=None):
    print("Starting Pipeline")
    print(user_id, lat, lon, totalframes, path, toggle_confidence)
    # Creates batch in database, with relevant details
    try: 
        new_batch(path, totalframes=totalframes, user_id=user_id, db=db)
        print("Succesfully created new batch")
    except Exception as e:
        print(e)
        print("Error Creating New Batch")

    #insert into Black and teal models


    # Uses ffmpeg to split individual frames from video
    try:
        lat = None
        lon = None
        if lat or lon is None:
            split_process(path, None, None, db=db, bid=bid)
        else:
            split_process(path, lat, lon, db=db,bid=bid)
        print("Succesfully processed vidoes/images/folder")
    except Exception as e:
        print("Error Processing Video")
        print(e)
        return "Error Processing Video"
    
    # Inferences frames through all enabled AI engines.
    make_inferences(db,tog,bid=bid, inspectionDate=inspectionDate, toggle_confidence=False)
    print("Succesfully made inferences")
    
    if bid is not None:
        db.batch.update_one({"batchID": bid}, {"$set": {"status": "completed"}})

# Re-annotate images
def reannotate(file_paths, labels, xyxy, db, batchIDs):
    image_ids = []
    print(labels, xyxy)
    # Get imageIDs based on file_paths
    for i, file_path in enumerate(file_paths):
        print(i, file_path)
        imageID_by_path_and_batch_pipeline = [
        {
            "$lookup": {
                "from": "batchImage",
                "localField": "imageID",
                "foreignField": "imageID",
                "as": "batchDetails"
            }
        },
        {
            "$match": {
                "batchDetails.batchID": int(batchIDs[i]),  # Convert batchID from string to int
                "imagePath": file_path
            }
        },
        {
            "$project": {
                "_id": 0,  # Exclude the _id field
                "imageID": 1  # Include the imageID field
            }
        }
    ]
        

        try:
            image = next(db.image.aggregate(imageID_by_path_and_batch_pipeline))
            print('image: ',image)

        except StopIteration:
            print(f"Image not found for file_path: {file_path}")
            continue
        if image:
            image_id = image['imageID']
            existing_defects = list(db.defect.find({"imageID": image_id}))
            existing_defect_labels = set(
                (d['outputLabel'].strip().lower(), d['imageID'], d['bbox']) for d in existing_defects
            )

            print('existing_defect_labels: ',existing_defect_labels)
            outputLabels = labels[i]
            bboxes = xyxy[i]
        
            new_defect_labels = set()
            for j, outputLabel in enumerate(outputLabels):
                outputLabel = outputLabel.title()
                normalized_label = outputLabel.strip().lower()
                defect_tuple = (normalized_label, image_id, str(bboxes[j]))
                
                new_defect_labels.add(defect_tuple)

                if defect_tuple not in existing_defect_labels:
                    # Insert new defect record if not already present
                    current_max = list(db.defect.find().sort('defectID', -1).limit(1))
                    db.defect.insert_one({
                        "defectID": int(current_max[0]['defectID']) + 1 if current_max else 1, 
                        "imageID": image_id,
                        "outputLabel": outputLabel,
                        "outputID": 17,
                        "bbox": str(bboxes[j]),
                        "confidence": 1,
                        "severity": 2
                    })
                    print(f"Inserted new defect for imageID: {image_id}, defectID: {int(current_max[0]['defectID']) + 1 if current_max else 1}, outputLabel: {outputLabel}")
            image_ids.append(image_id)
        else:  
            print(f"No image found for file_path: {file_path}")

        removed_defects = existing_defect_labels - new_defect_labels
        for defect in removed_defects:
            defectid = db.defect.find_one({
                    "imageID": defect[1], 
                    "outputLabel": defect[0],
                    "bbox": defect[2]
                    })['defectID']
            db.defect.delete_one({"imageID": defect[1], 
                                  "outputLabel": defect[0],
                                "bbox": defect[2]})
        
            image_path=db.image.find_one({"imageID": image_id})['imagePath']
            image_name = os.path.basename(image_path)
            image_name = image_name + "_" + defectid
            os.remove(os.path.join("active_learning", "unedited", image_name))

    for i in range(len(image_ids)):
        
        batch_path = db.batch.find_one({"batchID": int(batchIDs[i])})['batchPath']
        batch_name = os.path.basename(batch_path)
        print(batch_path)

        batch_name = batch_name[:-4]

        query = {"reportPath": {"$regex": batch_name}}
        projection = {"inspectionDate": 1, "_id": 0}
        insp_date = db.report.find_one(query, projection)
        insp_date = insp_date['inspectionDate'] if insp_date else None
        if insp_date==None:
            insp_date = datetime.now().strftime("%d/%m/%Y")
        apply_to_image(db, inspectionDate=insp_date, bid=None, image_id=image_ids[i], toggle_confidence=False, reannotating=True)
    


def save_to_csv(data, filename):
    """
    Save a list or pandas DataFrame to a CSV file.

    Parameters:
    - data: list or pandas DataFrame
    - filename: str, the name of the output CSV file
    """
    if isinstance(data, list):
        # Convert list to DataFrame
        df = pd.DataFrame(data)
    elif isinstance(data, pd.DataFrame):
        # Use the provided DataFrame
        df = data
    else:
        raise ValueError("Data should be either a list or a pandas DataFrame")
    
    # Save DataFrame to CSV
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")
