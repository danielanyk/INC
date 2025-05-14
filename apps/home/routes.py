#mo
import os
import time
import json
from apps.home import blueprint
from flask import (
    render_template,
    request,
    redirect,
    session,
    url_for,
    jsonify,
    send_from_directory
)
import zipfile
from flask_login import login_required
from jinja2 import TemplateNotFound
from apps.home.forms import ProductForm
from apps.home.models import Product, TaskResult, User, VideoProcessor
from celery.result import AsyncResult
from apps import mongo
from celery import current_app
import datetime
from datetime import datetime
from apps.config import Config
from apps.home.process import (pipeline,saving_reportdata,changing_reportdata)
from apps.home.report import (
    get_reports,
    get_filter_tags,
    view_report,
    generate_report,
    add_new_tags,
    get_amount_of_defects,
    get_bbox,
)
from apps.home.onemap_service import generate_static_map
from apps.home.config import ConfigData
import requests
import cv2
from pymongo import MongoClient
import matplotlib.pyplot as plt

# New imports for editor
import numpy as np
import base64
import ast
import shutil
import shlex
import imghdr
from datetime import datetime
import subprocess
import apps.home.state as state
from apps.home.process import reannotate
import dropbox
from apps.home.dropbox_authy import get_auth_flow
from functools import cache
client = MongoClient("mongodb://localhost:27017/FYP")


# db = client["FYP"]
db=client['newdb']
if ConfigData.DROPBOX_AUTH_TOKEN!="":
    dbx = dropbox.Dropbox(ConfigData.DROPBOX_AUTH_TOKEN)
blueprint.secret_key = "IFUCKINGHATEINCFUCKINCFUCKINCFUCKINCFUCKINCFUCKIAN6969696969696969699696969"

@blueprint.route('/check_defecttype_collection')
def check_defecttype_collection():
    collection_name = "defecttype"

    if collection_name in db.list_collection_names():
        return 'defecttype existing'
    else:
        db.create_collection(collection_name)

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
        }

        db[collection_name].insert_many([
            {"defecttypeid": _id, "defecttype": name} for name, _id in defect_classes.items()
        ])

        return "created defecttype"

@blueprint.route('/check_roles_collection')
def check_roles_collection():
    collection_name = "roles"

    if collection_name not in db.list_collection_names():
        roles_data = [
            {"roleid": 1, "role": "Admin"},
            {"roleid": 2, "role": "Inspector"}
        ]
        db[collection_name].insert_many(roles_data)

    # Return all roles
    roles = list(db[collection_name].find({}, {'_id': 0}))
    return jsonify(roles)

from werkzeug.security import generate_password_hash
@blueprint.route('/check_user_collection')
def check_user_collection():
    collection_name = "users"
    default_user = {
    "userid": 1,
    "roleid": 1,
    "username": "1",
    "firstname": "1",
    "lastname": "1",
    "password_hash": generate_password_hash("1")  # ✅ fix key name
}


    if collection_name in db.list_collection_names():
        # Collection exists, check if user with userid=1 exists
        if db.users.find_one({"userid": 1}):
            return "users existing"
        else:
            db.users.insert_one(default_user)
            return "inserted default user into existing users collection"
    else:
        # Create collection and insert default user
        db.create_collection(collection_name)
        db.users.insert_one(default_user)
        return "created users and inserted default user"

@blueprint.route("/")
@blueprint.route("/index")
@login_required
def index():
    try:
        bid = int(db.batch.find().sort("batchID", -1).limit(1)[0]["batchID"]) + 1
    except:
        bid = 1
    context = {
        "segment": "dashboard",
        "batchID": bid,
        "totalFrames": 0,
        "framesProcessed": 0,
    }
    return render_template("pages/index.html", **context)


@blueprint.route("/batch/<batchID>")
def batch(batchID):
    try:
        a = db.batch.find_one({"batchID": int(batchID)}, {"_id": 0})
        context = {
            "segment": "dashboard",
            "totalFrames": a["totalFrames"],
            "framesProcessed": a["framesProcessed"],
            "batchID": batchID,
        }
    except:
        context = {
            "segment": "dashboard",
            "totalFrames": 0,
            "framesProcessed": 0,
            "batchID": batchID,
        }
    return render_template("pages/index.html", **context)

# /batch/<batchID> batchID, methods=['POST']
# @blueprint.route("/makereport")
# def makereport():
#     # data = request.get_json()
#     # image_path = data.get('imagepath')
#     image_path = request.args.get('imgpath')
#     defect_type = request.args.get('defecttype')
#     defect_type=image_path.replace('.jpg','_'+defect_type+"_defect.jpg")
#     print(image_path)
#     return render_template("accounts/makereport.html", image_path=image_path,defect_type=defect_type)

from flask import send_file, abort
import os

@blueprint.route("/makereport")
def makereport():
    raw_path = request.args.get('imgpath')  # Full path
    defecttype = request.args.get('defecttype')
    status = request.args.get('status')
    lon=request.args.get('lon')
    lat=request.args.get('lat')
    print(defecttype)
    defect_label=defecttype.replace(' ',"_")
    # Construct URLs pointing to the custom serving route, image_url=image_url
    # image_url = url_for('home_blueprint.open_file', path=raw_path)
    defect_path = raw_path.replace('.jpg', f'_{defect_label}_defect.jpg')
    defect_url = url_for('home_blueprint.open_file', path=defect_path)
    # [:-4]
    imgpath=raw_path
    return render_template("accounts/makereport.html", defect_type=defect_url,image_path=imgpath,defecttype=defecttype,status=status,lat=lat,lon=lon)



@blueprint.route('/map')
def get_static_map():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return "Missing latitude or longitude", 400

    img_io = generate_static_map(lat, lon)
    if img_io:
        return send_file(img_io, mimetype='image/png')
    return "Failed to fetch map", 500

@blueprint.route('/openfile')
def open_file():
    filepath = request.args.get('path')  # full path like C:\Users\...\image.jpg
    if not filepath or not os.path.isfile(filepath):
        return abort(404)
    return send_file(filepath)
# @blueprint.route('/load_image')
# def load_image():
#     path = request.args.get('path')
#     if not path:
#         return "No path provided", 400
#     try:
#         return send_file(path, mimetype='image/jpeg')
#     except Exception as e:
#         return f"Error loading file: {e}", 500
    
# @blueprint.route('/load_image2')
# def load_image2():
#     path = request.args.get('path')
#     defect_type = request.args.get('defect_type')
#     # path=path.replace('.jpg','_'+defect_type+"_defect.jpg")
#     print("Path:", path)
#     print("Defect Type:", defect_type)
    
#     # Do something with both...
#     try:
#         return send_file(path, mimetype='image/jpeg')
#     except Exception as e:
#         return f"Error loading file: {e}", 500

@blueprint.route("/submit_report", methods=['POST'])
def submit_report():
    data=request.json
    
    print('request submitted')
    if "unchecked" in data["defectstatus"]:
        print("saving_report")
        saving_reportdata(db, data)
    else:
        print("changing_report")
        changing_reportdata(db,data)
    return jsonify({"message": "success"})

@blueprint.route("/starter")
def starter():
    return render_template("pages/starter.html")


@blueprint.route("/tables", methods=["GET", "POST"])
def datatables():
    form = ProductForm()
    products = Product.get_list()

    if request.method == "POST":
        form_data = {}
        for attribute, value in request.form.items():
            if attribute == "csrf_token":
                continue

            form_data[attribute] = value

        product = Product(**form_data)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for("home_blueprint.datatables"))

    context = {}
    context["parent"] = "apps"
    context["segment"] = "datatables"
    context["form"] = form
    context["products"] = products
    return render_template("pages/datatables.html", **context)


@blueprint.route("/update_batch_table", methods=["GET"])
def update_table():
    batches = db.batch.find({}, {"_id": 0})
    batches_list = []
    for batch in batches:
        user = db.user.find_one(
            {"userID": batch["userID"]}, {"_id": 0, "displayname": 1}
        )
        if user:
            batch["displayname"] = user["displayname"]
        else:
            batch["displayname"] = "User"
        batches_list.append(batch)
    return jsonify(batches_list)

#kyui
# @cache
@blueprint.route("/update_image_table/<batchID>", methods=["GET"])
def update_image_table(batchID):
    batchID = int(batchID)
    # pipeline = [
       
    #             "severity": {"$push": "$defects.severity"}, {
    #         "$lookup": {
    #             "from": "batchImage",
    #             "localField": "imageID",
    #             "foreignField": "imageID",
    #             "as": "batch_info",
    #         }
    #     },
    #     {"$unwind": "$batch_info"},
    #     {"$match": {"batch_info.batchID": batchID}},
    #     {
    #         "$lookup": {
    #             "from": "defect",
    #             "localField": "imageID",
    #             "foreignField": "imageID",
    #             "as": "defects",
    #         }
    #     },
    #     {"$unwind": {"path": "$defects", "preserveNullAndEmptyArrays": False}},
    #     {"$sort": {"_id": 1}},
    #     {
    #         "$group": {
    #             "_id": "$imageID",
    #             "imagePath": {"$first": "$imagePath"},
    #             "location": {
    #                 "$first": {
    #                     "town": "$town",
    #                     "block": "$block",
    #                     "road": "$road",
    #                     "roadType": "$roadType",
    #                 }
    #             },
    #             "defects": {"$push": "$defects.outputLabel"},
    #             "outputID": {"$push": "$defects.outputID"},
    #         }
    #     },
    #     {
    #         "$project": {
    #             "_id": 0,
    #             "imagePath": 1,
    #             "imageID": "$_id",
    #             "location": {"$concat": ["$location.town"]},
    #             "outputID": 1,
    #             "defects": 1,
    #             "severity": 1,
    #         }
    #     },
    # ]

    #MOST ORIGINAL ONE
#     pipeline = [
#     {
#         "$lookup": {
#             "from": "batchImage",
#             "localField": "imageID",
#             "foreignField": "imageID",
#             "as": "batch_info",
#         }
#     },
#     {"$unwind": "$batch_info"},
#     {"$match": {"batch_info.batchID": batchID}},
#     {
#         "$lookup": {
#             "from": "defect",
#             "localField": "imageID",
#             "foreignField": "imageID",
#             "as": "defects",
#         }
#     },
#     {"$unwind": {"path": "$defects", "preserveNullAndEmptyArrays": False}},
#     {"$sort": {"_id": 1}},
#     {
#         "$group": {
#             "_id": "$imageID",
#             "imagePath": {"$first": "$imagePath"},
#             "location": {
#                 "$first": {
#                     "town": "$town",
#                     "block": "$block",
#                     "road": "$road",
#                     "roadType": "$roadType",
#                 }
#             },
#             "defects": {"$push": "$defects.outputLabel"},
#             "outputID": {"$push": "$defects.outputID"},
#             "severity": {"$push": "$defects.severity"},  # <== this is now correctly inside $group
#         }
#     },
#    {
#         "$project": {
#             "_id": 0,
#             "imagePath": 1,
#             "imageID": "$_id",
#             "location": {"$concat": ["$location.town"]},
#             "outputID": 1,
#             "defects": 1,
#             "severity": 1,
#         }
#     }, 
    


# ]
##version before blacks onemap
#     pipeline = [
#     {
#         "$lookup": {
#             "from": "batchImage",
#             "localField": "imageID",
#             "foreignField": "imageID",
#             "as": "batch_info",
#         }
#     },
#     {"$unwind": "$batch_info"},
#     {"$match": {"batch_info.batchID": batchID}},
#     {
#         "$lookup": {
#             "from": "defect",
#             "localField": "imageID",
#             "foreignField": "imageID",
#             "as": "defects",
#         }
#     },
#     {"$unwind": {"path": "$defects", "preserveNullAndEmptyArrays": False}},
#     {"$sort": {"_id": 1}},
#     {
#         "$group": {
#             "_id": "$imageID",
#             "imagePath": {"$first": "$imagePath"},
#             "location": {
#                 "$first": {
#                     "town": "$town",
#                     "block": "$block",
#                     "road": "$road",
#                     "roadType": "$roadType",
#                 }
#             },
#             "defects": {"$push": "$defects.outputLabel"},
#             "outputID": {"$push": "$defects.outputID"},
#             "severity": {"$push": "$defects.severity"},
#         }
#     },
#     {
#         "$unwind": "$outputID"
#     },
#     {
#         "$addFields": {
#             "outputID_str": { "$toString": "$outputID" }
#         }
#     },
#     {
#         "$lookup": {
#             "from": "report",
#             "let": { "imageID": "$_id", "outputID_str": "$outputID_str" },
#             "pipeline": [
#                 {
#                     "$match": {
#                         "$expr": {
#                             "$and": [
#                                 { "$eq": ["$imageID", "$$imageID"] },
#                                 { "$eq": ["$defectNumber", "$$outputID_str"] }
#                             ]
#                         }
#                     }
#                 },
#                 { "$project": { "status": 1, "_id": 0 } }
#             ],
#             "as": "report_info"
#         }
#     },
#     {
#         "$unwind": {
#             "path": "$report_info",
#             "preserveNullAndEmptyArrays": True
#         }
#     },
#     {
#         "$group": {
#             "_id": "$_id",
#             "imagePath": { "$first": "$imagePath" },
#             "location": { "$first": "$location" },
#             "defects": { "$push": "$defects" },
#             "outputID": { "$push": "$outputID" },
#             "severity": { "$push": "$severity" },
#             "status": { "$push": "$report_info.status" }
#         }
#     },
#     # ✅ Add sort here
#     {
#         "$sort": { "imagePath": 1 }
#     },
#     {
#         "$project": {
#             "_id": 0,
#             "imagePath": 1,
#             "imageID": "$_id",
#             "location": { "$concat": ["$location.town"] },
#             "outputID": 1,
#             "defects": 1,
#             "severity": 1,
#             "status": 1  
#         }
#     }
# ]

    pipeline = [
        {
            "$lookup": {
                "from": "batchImage",
                "localField": "imageID",
                "foreignField": "imageID",
                "as": "batch_info",
            }
        },
        {"$unwind": "$batch_info"},
        {"$match": {"batch_info.batchID": batchID}},
        {
            "$lookup": {
                "from": "defect",
                "localField": "imageID",
                "foreignField": "imageID",
                "as": "defects",
            }
        },
        {"$unwind": {"path": "$defects", "preserveNullAndEmptyArrays": False}},
        {"$sort": {"_id": 1}},
        {
            "$group": {
                "_id": "$imageID",
                "imagePath": {"$first": "$imagePath"},
                "location": {
                    "$first": {
                        "town": "$town",
                        "block": "$block",
                        "road": "$road",
                        "roadType": "$roadType",
                    }
                },
                "longitude": {"$first": "$longitude"},
                "latitude": {"$first": "$latitude"},
                "defects": {"$push": "$defects.outputLabel"},
                "outputID": {"$push": "$defects.outputID"},
                "severity": {"$push": "$defects.severity"},
            }
        },
        {
            "$unwind": "$outputID"
        },
        {
            "$addFields": {
                "outputID_str": { "$toString": "$outputID" }
            }
        },
        {
            "$lookup": {
                "from": "report",
                "let": { "imageID": "$_id", "outputID_str": "$outputID_str" },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    { "$eq": ["$imageID", "$$imageID"] },
                                    { "$eq": ["$defectNumber", "$$outputID_str"] }
                                ]
                            }
                        }
                    },
                    { "$project": { "status": 1, "_id": 0 } }
                ],
                "as": "report_info"
            }
        },
        {
            "$unwind": {
                "path": "$report_info",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "imagePath": { "$first": "$imagePath" },
                "location": { "$first": "$location" },
                "longitude": { "$first": "$longitude" },
                "latitude": { "$first": "$latitude" },
                "defects": { "$push": "$defects" },
                "outputID": { "$push": "$outputID" },
                "severity": { "$push": "$severity" },
                "status": { "$push": "$report_info.status" }
            }
        },
        {
            "$sort": { "imagePath": 1 }
        },
        {
            "$project": {
                "_id": 0,
                "imagePath": 1,
                "imageID": "$_id",
                "location": { "$concat": ["$location.town"] },
                "longitude": 1,
                "latitude": 1,
                "outputID": 1,
                "defects": 1,
                "severity": 1,
                "status": 1
            }
        }
    ]

    results = db.image.aggregate(pipeline)
# {
#     "$project": {
#         "_id": 0,
#         "imagePath": {
#             "$concat": [
#                 { "$arrayElemAt": [{ "$split": ["$imagePath", "."] }, 0] },
#                 "_defect.",
#                 { "$arrayElemAt": [{ "$split": ["$imagePath", "."] }, 1] }
#             ]
#         },
#         "imageID": "$_id",
#         "location": { "$concat": ["$location.town"] },
#         "outputID": 1,
#         "defects": 1,
#         "severity": 1,
#     }}
    image_table_list = list(results)
    # print(image_table_list[0])
    # print(image_table_list)
    return jsonify(image_table_list)

@blueprint.route('/dropbox_auth_finish')
def dropbox_auth_finish():
    try:
        print(session)
        result = get_auth_flow(session).finish(request.args)
        print(session,"here")
        access_token = result.access_token
        ConfigData.update_dropbox_auth_token(access_token)
        dbx = dropbox.Dropbox(access_token)
        return redirect('/')
    except Exception as e:
        return str(e)

@blueprint.route('/dropbox_auth_start')
def dropbox_auth_start():
    
    print(session)
    return redirect(get_auth_flow(session).start())

@blueprint.route("/open_onemap", methods=["GET"])
def open_onemap():
    print("Trying to open QGIS.")
    original_cwd = os.getcwd()
    try:
        print(os.getcwd())
        subprocess.run("run_qgis_setup.bat", shell=True, cwd="A_QGIS")
    finally:
        os.chdir(original_cwd)
    
    return jsonify("success")

@blueprint.route("/get_total_frames", methods=["GET"])
def get_total_frames():
    folder = request.args.get("folder")
    total_duration = 0
    tempdir = ConfigData.VIDEO_LOCATION
    print(tempdir, folder)
    for filename in os.listdir(os.path.join(tempdir, folder)):
        if filename.endswith((".mp4", ".mov", ".avi", ".mkv")):
            video = cv2.VideoCapture(os.path.join(tempdir, folder, filename))

            fps = video.get(cv2.CAP_PROP_FPS)

            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = int(frame_count / fps)
            total_duration += duration
    return jsonify(totalF=total_duration)

@blueprint.route("/start_process", methods=["POST"])
def process():
    data = request.json
    # lat = data['lat']
    # lon = data['lon']
    state.stop_flag = False
    total_frames = data["total_frames"] 
    file_path = data["path"]
    bid = data["bid"]
    print("request recieved")
    pipeline(
        db,
        inspectionDate=data["inspectionDate"],
        path=os.path.join(ConfigData.VIDEO_LOCATION, file_path),
        tog=data['toggle'],
        lon=None,
        lat=None,
        totalframes=total_frames,
        bid=bid
        
    )

    return jsonify({"status": "success"})

@blueprint.route('/stop_process', methods=['POST'])
def stop_process():
    state.stop_flag=True  # Set flag
    print("stop request sent")
    return jsonify({"status": "stopping"})


@blueprint.route('/get_image_details/<id>')
def get_image_details(id):
    id = int(id)
    image_details = db.image.find_one({"imageID": id})
    
    if image_details:

        image_details.pop('_id', None)
        return jsonify(image_details)
    else:
        return jsonify({"error": "Image not found"}), 404


@blueprint.route("/Batches/<path:filename>")
def serve_file(filename):
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    batches_dir = os.path.join(basedir, "Batches")
    return send_from_directory(batches_dir, filename)



@blueprint.route("/batchStatus/<batchID>", methods=["GET"])
def batchStatus(batchID):
    batchID = int(batchID)
    batch = db.batch.find_one({"batchID": batchID})
    if batch:
        return jsonify(
            {
                "status": batch.get("status"),
                "framesProcessed": batch.get("framesProcessed"),
            }
        )
    else:
        return jsonify({"framesProcessed": 0, "status": "Waiting"})


@blueprint.route("/charts/", methods=["GET"])
def charts():
    products = [
        {"name": product.name, "price": product.price} for product in Product.get_list()
    ]
    context = {}
    context["parent"] = "apps"
    context["segment"] = "charts"
    context["products"] = products
    return render_template("pages/charts.html", **context)


@blueprint.route("/run_script", methods=["POST"])
def run_script_route():
    from apps.home.tasks import write_to_log_file
    task_results_collection = db.task_result
    def run_script(script_path):
        start_time = datetime.now()
        process = subprocess.Popen(f"python {script_path}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(8)

        exit_code = process.wait()
        error = False
        status = "STARTED"
        if exit_code == 0:
            logs = process.stdout.read().decode()
            status = "SUCCESS"
        else:
            logs = process.stderr.read().decode()
            error = True
            status = "FAILURE"
        log_file = write_to_log_file(logs, script_path.split('/')[-1])

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        task_result = {
            "task_name": "execute_script",
            "periodic_task_name": script_path,
            "status": status,  # Use status.value to get the string representation from the Enum
            "date_created":start_time,
            "date_done": end_time,
            "result": f"Execution time: {execution_time} seconds"
        }

        task_results_collection.insert_one(task_result)

        return jsonify({"logs": logs, "input": script_path, "error": error, "output": "", "status": status, "log_file": log_file})

    script_name = request.form["script"]
    file_path = os.path.join(Config.CELERY_SCRIPTS_DIR, script_name)
    if os.path.isfile(file_path):
        run_script(file_path)

    return redirect(url_for("home_blueprint.tasks"))


@blueprint.route('/tasks', methods=['GET', 'POST'])
def tasks():
    from apps.home.tasks import get_scripts
    task_results_collection = db.task_result
    scripts, ErrInfo = get_scripts()
    context = {
        'cfgError' : ErrInfo,
        'scripts'  : scripts,
        'tasks'	   : TaskResult.get_latest(),
        'segment'  : 'tasks',
        'parent'   : 'apps',
    }
    # task_results = TaskResult.get_all()
    task_results = list(task_results_collection.find())
    context["task_results"] = task_results
    return render_template("pages/tasks.html", **context)


# Custom Filter
@blueprint.app_template_filter("get_result_field")
def get_result_field(result, field: str):
    result = json.loads(result.result)
    if result:
        return result.get(field)


@blueprint.app_template_filter("date_format")
def date_format(date):
    try:
        return date.strftime(r"%Y-%m-%d %H:%M:%S")
    except:
        return date


@blueprint.app_template_filter("name_from_path")
def name_from_path(path):
    try:
        name = path.split("/")[-1]
        return name
    except:
        return path
    

# START OF REPORT ROUTES

@blueprint.route("/update_report", methods=["POST"])
def edit_report():
    data = request.json

    report_id = data.get('report_id') 
    quantity = data.get('quantity')
    measurement = data.get('measurement')
    cause = data.get('cause')
    recommendation = data.get('recommendation')
    remarks = data.get('remarks')
    supervisor = data.get('supervisor')
    via = data.get('via')
    acknowledgement = data.get('acknowledgement')

    update_data = {
        "$set": {
            "generationTime": datetime.now().strftime("%d %b %Y, %H:%M:%S"),
            "quantity": quantity,
            "measurement": measurement,
            "cause": cause,
            "recommendation": recommendation,
            "remarks": remarks,
            "supervisor": supervisor,
            "via": via,
            "acknowledgement": acknowledgement
        }
    }

    # Perform the update operation
    result = db.report.update_one({"reportID": report_id}, update_data)

    if result.matched_count == 0:
        return jsonify({"message": "Report not found"}), 404

    return jsonify({"message": "success"})


@blueprint.route("/report", methods=["GET"])
def report():
    batch, defects, town_tags, custom_tags = get_filter_tags()

    return render_template(
        "pages/report.html",
        batches=batch,
        defects=defects,
        town_tags=town_tags,
        custom_tags=custom_tags,
    )

# get reports with the filters
@blueprint.route("/get_reports", methods=["POST"])
def get_reports_route():
    data = request.json
    batch = data.get("batches")
    defect_type = data.get("defects")
    severity = data.get("severity")
    custom_tags = data.get("custom_tags")
    location = data.get("location")
    start_date = data.get("startDate")
    end_date = data.get("endDate")

    if batch == "":
        batch = None
    if defect_type == "":
        defect_type = None
    if severity == "":
        severity = None
    if custom_tags == "":
        custom_tags = None
    if location == "":
        location = None
    if start_date == "Invalid date":
        start_date = None
    if end_date == "undefined":
        end_date = None
    print(start_date)
    print(end_date)

    tags = {
        "Batch": batch,
        "Defect Type": defect_type,
        "Severity": int(severity) if severity else None,
        "Custom Tag": custom_tags,
        "Location": location,
        "DateStart": start_date,
        "DateEnd": end_date,
    }
    print(tags)
    reports = get_reports(tags)
    return jsonify(reports)
#use this to view report
@blueprint.route("/get_reportPath/<imageID>/<defect>", methods=["GET"])
def get_reportPath(imageID,defect):
    imageID = int(imageID)
    print(defect)
    # print(index)
    report = db.report.find_one({"imageID": imageID,"defectNumber":defect})
    if report:
        print(report["reportPath"])
        return jsonify({"reportPath": report["reportPath"]})
    else:
        return jsonify({"reportPath": None})

@blueprint.route("/view_temp", methods=["POST"])
def view_temp():
    data = request.json
    print(data)
    view_report(data["path"])
    return jsonify("success")
# 
# @blueprint.route("/viewreport")
# def viewreport():
#     defecttype = request.args.get('defecttype')
#     imageID = int(request.args.get('imageID'))
#     print(imageID)
#     pipeline = [
#     {
#         "$match": {
#             "imageID": imageID
#         }
#     },
#     {
#         "$lookup": {
#             "from": "defect",
#             "let": { "reportDefectNumber": "$defectNumber" },
#             "pipeline": [
#                 {
#                     "$match": {
#     "$expr": {
#         "$and": [
#             { "$eq": ["$imageID", imageID] },
#             {
#                 "$regexMatch": {
#                     "input": "$outputLabel",
#                     "regex": defecttype,
#                     "options": "i"
#                 }
#             },
#             { "$eq": [{ "$toString": "$outputID" }, "$$reportDefectNumber"] }
#         ]
#     }
# }

#                 }
#             ],
#             "as": "matchedDefects"
#         }
#     },
#     {
#         "$match": {
#             "matchedDefects.0": { "$exists": True }
#         }
#     },
#     {
#         "$project": {
#             "_id": 0,
#             "reportPath": 1
#         }
#     }
# ]


#     results = list(db.report.aggregate(pipeline))
#     print(results)
from flask import request, redirect, jsonify

@blueprint.route("/viewreport")
def viewreport():
    defecttype = request.args.get('defecttype')
    imageID = int(request.args.get('imageID'))
    print(imageID)

    pipeline = [
        {
            "$match": {
                "imageID": imageID
            }
        },
        {
            "$lookup": {
                "from": "defect",
                "let": { "reportDefectNumber": "$defectNumber" },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    { "$eq": ["$imageID", imageID] },
                                    {
                                        "$regexMatch": {
                                            "input": "$outputLabel",
                                            "regex": defecttype,
                                            "options": "i"
                                        }
                                    },
                                    { "$eq": [{ "$toString": "$outputID" }, "$$reportDefectNumber"] }
                                ]
                            }
                        }
                    }
                ],
                "as": "matchedDefects"
            }
        },
        {
            "$match": {
                "matchedDefects.0": { "$exists": True }
            }
        },
        {
            "$project": {
                "_id": 0,
                "reportPath": 1
            }
        }
    ]

    results = list(db.report.aggregate(pipeline))
    print(results)

    if len(results) > 1:
        results = results[-1]
    elif results:
        results = results[0]
    else:
        return jsonify("no results"), 404

    view_report(results["reportPath"])

    # Redirect back to previous page
    return redirect(request.referrer or "/")

#     print(list(db.report.aggregate([
#     { "$match": { "imageID": int(imageID) } }
# ])))



    if len(results)>1:
        results=results[-1]
    else:
        results=results[0]
    view_report(results["reportPath"])
    return jsonify("success")

# @blueprint.route("/viewreport")
# def viewreport():
#     defecttype = request.args.get('defecttype')
#     imageID = int(request.args.get('imageID'))

#     pipeline = [
#         { "$match": { "imageID": imageID } },
#         { "$lookup": {
#             "from": "defect",
#             "let": { "reportDefectNumber": "$defectNumber" },
#             "pipeline": [
#                 { "$match": {
#                     "$expr": {
#                         "$and": [
#                             { "$eq": ["$imageID", imageID] },
#                             { "$regexMatch": {
#                                 "input": "$outputLabel",
#                                 "regex": defecttype,
#                                 "options": "i"
#                             }},
#                             { "$eq": [{ "$toString": "$outputID" }, "$$reportDefectNumber"] }
#                         ]
#                     }
#                 }}
#             ],
#             "as": "matchedDefects"
#         }},
#         { "$match": { "matchedDefects.0": { "$exists": True } }},
#         { "$project": { "_id": 0, "reportPath": 1 } }
#     ]

#     results = list(db.report.aggregate(pipeline))
#     if len(results) > 1:
#         results = results[-1]
#     else:
#         results = results[0]

#     return send_file(results["reportPath"], as_attachment=False)



@blueprint.route("/generate_report", methods=["POST"])
def generate_report_route():
    data = request.json
    selected_template = data["template"][-1]
    bbox = get_bbox(data["imageID"])
    report_data = {
        "name": data["name"],
        "ins_type": data["ins_type"],
        "ins_date": data["ins_date"],
        "road_type": data["road_type"],
        "type": data["type"],
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "inspector": data["inspector"],
        "severity": data["severity"],
        "image": data["image"],
        "report_id": data["report_id"],
        "road": data["road"],
        "quantity": data["quantity"],
        "measurement": data["measurement"],
        "cause": data["cause"],
        "recommendation": data["recommendation"],
        "remarks": data["remarks"],
        "supervisor": data["supervisor"],
        "via": data["via"],
        "acknowledgement": data["acknowledgement"],
        "bbox": bbox,
    }
    if data["placeholder"] == 'download':
        path = generate_report(report_data, selected_template, 'download')
    else:
        path = generate_report(report_data, selected_template, 'temp')

    return jsonify(path)


@blueprint.route("/add_tags", methods=["POST"])
def add_tags():
    data = request.json
    report_id = data["report_id"]
    tags = data["tags"]

    return jsonify(add_new_tags(report_id, tags))


@blueprint.route("/load_more", methods=["POST"])
def load_more():
    data = request.json
    batch = data.get("batches")
    defect_type = data.get("defects")
    severity = data.get("severity")
    custom_tags = data.get("custom_tags")
    location = data.get("location")
    start_date = data.get("startDate")
    end_date = data.get("endDate")
    startindex = data.get("startindex")
    endindex = data.get("endindex")

    if batch == "":
        batch = None
    if defect_type == "":
        defect_type = None
    if severity == "":
        severity = None
    if custom_tags == "":
        custom_tags = None
    if location == "":
        location = None
    if start_date == "Invalid date":
        start_date = None
    if end_date == "undefined":
        end_date = None
    
    print(start_date)
    print(end_date)

    tags = {
        "Batch": batch,
        "Defect Type": defect_type,
        "Severity": int(severity) if severity else None,
        "Custom Tag": custom_tags,
        "Location": location,
        "DateStart": start_date,
        "DateEnd": end_date,
    }

    reports = get_reports(tags, startindex, endindex)
    return jsonify(reports)


@blueprint.route("/get_defect_count", methods=["GET"])
def get_defect_tags():
    defect_count = get_amount_of_defects()
    return jsonify(defect_count)


@blueprint.route("/download", methods=["POST"])
def download():
    def download_file_from_shared_link(shared_link, local_path):
        """Download a file from Dropbox using a shared link."""
        try:
            dbx.sharing_get_shared_link_file_to_file(download_path=local_path, url=shared_link)
            return local_path
        except Exception as e:
            return str(e)


    def download_folder_from_shared_link(path, local_folder_path):
        """Download a folder from Dropbox using a shared link."""
        try:
            # Define the local zip file path
            local_zip_path = os.path.join(local_folder_path, "folder.zip")

            # Download the folder as a zip file
            dbx.files_download_zip_to_file(local_zip_path, path)

            # Unzip the downloaded file
            with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(local_folder_path))

            # Delete the zip file after extraction
            os.remove(local_zip_path)

            return local_folder_path
        except Exception as e:
            print(str(e))
            return str(e)

    data = request.json
    shared_link = data.get('dropbox_path')
    local_filename = data.get('name')
    fid=data.get('id')
    local_path = os.path.join(ConfigData.VIDEO_LOCATION, local_filename)

    if data.get('is_folder'):
        os.makedirs(local_path, exist_ok=True)
        print(local_path)
        result = download_folder_from_shared_link(fid, local_path)
    else:
        result = download_file_from_shared_link(shared_link, local_path)

    if os.path.exists(result):
        return jsonify({"message": "Download successful", "local_path": local_path})
    else:
        return jsonify({"error": result}), 500


@blueprint.route("/shutdown", methods=["POST"])
def shutdown():
    subprocess.run("cmd.exe /k ./apps/home/Engines/shutdown.bat", shell=True)

# END OF REPORT ROUTES

# START OF SUMMARIZATION ROUTES
@blueprint.route('/summarize', methods=['POST'])
def summarize():
    try:
        content = request.json.get('content')
        style = request.json.get('style')
        language = request.json.get('language', 'Default')
        
        print('style', style)

        if style == 'Numbered List':
            style = 'List'
        elif style == 'One Sentence':
            style = 'One sentence'
        elif style not in ['One Sentence', 'Consise', 'Detailed', 'Numbered List']:
            style = 'Detailed'
        
        input_data = {
            "content": content,
            "style": style,
            "language": language
        }
        print(input_data)

        response = requests.post("http://localhost:5007/summarize", json=input_data)
        
        if response.status_code == 200:
            response_json = response.json()
            summary = response_json.get("summary", "No summary found")
            info = response_json.get("info", "No additional info")
            return jsonify({"summary": summary, "info": info})
        else:
            return jsonify({"error": "Summarizer service returned an error", "status_code": response.status_code}), response.status_code
        
    except Exception as e:
        # # Log the error
        # print(f"There's an issue with the summarizer: {e}")
        return jsonify({"error": "There's an issue with the summarizer","content":input_data}), 500


# END OF SUMMARIZATION ROUTES

###########################################################################################################################################
# START OF ANNOTATOR ROUTES
# RMB TO CHANGE PATH IF NECESSARY
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
@blueprint.route('/open_annotator', methods=['POST'])
def open_annotator():
    data = request.json  # Assuming the list of filepaths is sent as a JSON array
    print(data)

    file_paths = data['selectedItems']
    batchIDs = data['batchNumbers']
    bboxes = data['bboxes']
    labels = data['defectLabels']
    # print(batchIDs)
    # print(bboxes)
    # print(labels)
    json_annotations = []

    if not file_paths:  # Check if the list is empty
        return "No file paths provided"
    # Validate each file path
    for i, path in enumerate(file_paths):
        full_path = os.path.join(root_dir, 'Batches', path)
    
        # Initialize json_data for each image file
        json_data = {
            'version': '5.5.0',
            'flags': {},
            'shapes': [],
            'imagePath': path,
            'imageData': encode_image_to_base64(full_path)
        }
    
        # loop over bboxes[i] and create json files for each bbox
        for j, bbox in enumerate(bboxes[i]):
            # convert bbox from a string to an array
            if bbox != '':
                bbox_arr = np.array(ast.literal_eval(bbox))
                annots = [
                    [bbox_arr[0], bbox_arr[1]],
                    [bbox_arr[2], bbox_arr[3]]
                ]
                label = labels[i][j]
                shape_type = 'rectangle'
                json_data['shapes'].append({
                    'label': label,
                    'points': annots,
                    'group_id': None,  # might have to change this
                    'shape_type': shape_type,
                    'flags': {}
                })
    
        # Append json_data for the current image to json_annotations
        json_annotations.append(json_data)
        
        if not os.path.isfile(os.path.join(root_dir, 'Batches', path)) or imghdr.what(os.path.join(root_dir, 'Batches', path)) is None:  # Check if the file exists
            return f"File not found: {path}"
        else:
            file_paths[i] = full_path

    # Create temp directory and save files in temp directory
    tempdir = os.path.join(root_dir, "temp")
    if os.path.exists(tempdir):
         shutil.rmtree(tempdir)
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
        
    for k, file_path in enumerate(file_paths):
        # Save json file in temp directory
        if len(json_annotations[k]['shapes']) != 0:
            json_path = os.path.join(tempdir, os.path.basename(file_path).replace('.jpg', '.json'))
            with open(json_path, 'w') as json_file:
                json.dump(json_annotations[k], json_file)
        destination_path = os.path.join(tempdir, os.path.basename(file_path))
        shutil.copy(file_path, destination_path)

    # TO RUN EXE
    # # Command to open all files with LabelImg, RMB TO CHANGE LabelImg DIRECTORY TO LABELME DIRECTORY
    directory = r"temp"
    directory_quoted = shlex.quote(directory)

    subprocess.run(['Labelme.exe', '--labels', 'labels.txt', directory_quoted], shell=True)

        # # Uncomment if labelImg is used instead of labelme
        # venv_activate_path = r"bruh\Scripts\activate.bat"  # Adjust this path to your virtual environment path
        # labelImg_dir = r"labelImg\labelImg.py"
        # defects_file = r'labelImg\defects.txt'
        # resources_file = r'labelImg\libs\resources.py'
        # qrc_file = r'labelImg\resources.qrc' 
        # resources_file_quoted = shlex.quote(resources_file)
        # qrc_file_quoted = shlex.quote(qrc_file)
        # labelImg_dir_quoted = shlex.quote(labelImg_dir)
        # defects_file_quoted = shlex.quote(defects_file)
        # subprocess.run(f'cmd /K "{venv_activate_path} && pyrcc5 -o {resources_file} {qrc_file}"', shell=True)
        # subprocess.run(f'cmd /K "{venv_activate_path} && python {labelImg_dir} {directory} {defects_file}"', shell=True)

    # Read from json/xml file(s) somewhere (in temp folder)
    labels = []
    xyxy = []
    paths_to_process = []

    for file in os.listdir(tempdir):
        if file.endswith(".json"):
            print('file: ',file)
            label = []
            coords = []
            json_path = os.path.join(tempdir, file)
            file_basename_without_ext = os.path.splitext(file)[0]

            # Check if the basename matches with any in file_paths
            for file_path in file_paths:
                file_path_basename_without_ext = os.path.splitext(os.path.basename(file_path))[0]
                if file_basename_without_ext == file_path_basename_without_ext:
                    paths_to_process.append(file_path)  # Append the full filepath

            with open(json_path, 'r') as f:
                data = json.load(f)
                for annotation in data['shapes']:
                    print(annotation['label'])
                    label.append(annotation['label'])
                    combined_points = annotation['points'][0] + annotation['points'][1]
                    print('bbox: ',combined_points)
                    coords.append(combined_points)
                
            labels.append(label)
            xyxy.append(coords)
            print('labels:',labels)
            print('xyxy: ',xyxy)

    # Run reannotation pipeline
    reannotate(paths_to_process, labels, xyxy, db, batchIDs)
        # Update db pipeline: 
        # enumerate through file_paths, get imageID from image table where file_path = file_path
        # aggregate image and defect table by image.imageID = defect.imageID,
        # then delete all where imageID in imageIDs in defect table
        # then insert new defects with fields required:
        # imageID, outputLabel, confidence=1, bbox (from json), severity=2 (for now)
        # where outputLabel = labels[i], bbox = xyxy[i], and labels and xyxy are arrays of the correct format

    # Delete temp directory
    shutil.rmtree(tempdir)
    return "success"
    
@blueprint.route("/update_editor_table", methods=['GET'])
def update_editor_table(start=0, end=30):
    pipeline = [
    {
        "$lookup": {
            "from": "defect",  # Join with the "defect" collection
            "localField": "imageID",  # Field from the "image" collection
            "foreignField": "imageID",  # Field from the "defect" collection
            "as": "defects"  # The array to hold the joined documents
        }
    },
    {
        "$lookup": {
            "from": "batchImage",  # Join with the "batchImage" collection
            "localField": "imageID",  # Field from the "image" collection
            "foreignField": "imageID",  # Field from the "batchImage" collection
            "as": "batchInfo"  # The array to hold the joined documents
        }
    },
    {
        "$project": {
            "_id": 0,
            "imageID": 1,
            "imagePath": 1,
            "defects": {
                "$map": {
                    "input": "$defects",
                    "as": "defect",
                    "in": {
                        "outputLabel": "$$defect.outputLabel",  # Keep the outputLabel
                        "bbox": "$$defect.bbox"  # Include the bbox field
                    }
                }
            },
            "batchID": {
                "$arrayElemAt": ["$batchInfo.batchID", 0]  # Assuming each imageID is linked to one batchID, extract the first batchID
            }
        }
    }
]

    results = db.image.aggregate(pipeline)
    return jsonify(list(results)[start:end])

@blueprint.route("/get_filtered_results", methods=['GET'])
def get_filtered_results(startDate, endDate, defectList, start=0, end=30):
    print(startDate, endDate, defectList)
    if (len(startDate) == 0 or len(endDate) == 0) and defectList == []:
        pipeline = [
        {
            "$lookup": {
                "from": "defect",  # Join with the "defect" collection
                "localField": "imageID",  # Field from the "image" collection
                "foreignField": "imageID",  # Field from the "defect" collection
                "as": "defects"  # The array to hold the joined documents
            }
        },
        {
            "$lookup": {
                "from": "batchImage",  # Join with the "batchImage" collection
                "localField": "imageID",  # Field from the "image" collection
                "foreignField": "imageID",  # Field from the "batchImage" collection
                "as": "batchInfo"  # The array to hold the joined documents
            }
        },
        {
            "$project": {
                "_id": 0,
                "imageID": 1,
                "imagePath": 1,
                "defects": {
                    "$map": {
                        "input": "$defects",
                        "as": "defect",
                        "in": {
                            "outputLabel": "$$defect.outputLabel",  # Keep the outputLabel
                            "bbox": "$$defect.bbox"  # Include the bbox field
                        }
                    }
                },
                "batchID": {
                    "$arrayElemAt": ["$batchInfo.batchID", 0]  # Assuming each imageID is linked to one batchID, extract the first batchID
                }
            }
        }
    ]
    elif len(startDate) == 0 or len(endDate) == 0:
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
        "$lookup": {
            "from": "batchImage",
            "localField": "imageID",
            "foreignField": "imageID",
            "as": "batchInfo"
        }
    },
    {
        "$addFields": {
            "hasRelevantDefect": {
                "$anyElementTrue": {
                    "$map": {
                        "input": "$defects",
                        "as": "defect",
                        "in": {"$in": ["$$defect.outputLabel", defectList]}
                    }
                }
            }
        }
    },
    {
        "$match": {
            "hasRelevantDefect": True
        }
    },
    {
        "$project": {
            "_id": 0,
            "imageID": 1,
            "imagePath": 1,
            "hasRelevantDefect": 1,
            "defects": {
                "$filter": {
                    "input": "$defects",
                    "as": "defect",
                    "cond": {"$in": ["$$defect.outputLabel", defectList]}
                }
            },
            "defects": {
                "$map": {
                    "input": "$defects",
                    "as": "defect",
                    "in": {
                        "outputLabel": "$$defect.outputLabel",
                        "bbox": "$$defect.bbox"
                    }
                }
            },
            "batchID": {
                "$arrayElemAt": ["$batchInfo.batchID", 0]
            },
        }
    }
]
        
    else:
        # Parse the startDate and endDate using the existing format
        start_date_obj = datetime.datetime.strptime(startDate, "%Y-%m-%d")
        end_date_obj = datetime.datetime.strptime(endDate, "%Y-%m-%d")

        # Add a time component of "00:00:00" to each date
        start_date_with_time = datetime.datetime.combine(start_date_obj, datetime.time(0, 0, 0))
        end_date_with_time = datetime.datetime.combine(end_date_obj, datetime.time(0, 0, 0))

        # Format the datetime objects using the new format string
        formatted_start_date = start_date_with_time.strftime("%d %B %Y, %H:%M:%S")
        formatted_end_date = end_date_with_time.strftime("%d %B %Y, %H:%M:%S")
        if defectList == []:
            pipeline = [
            {
                "$match": {
                    "datetime": {  # This field should match the datetime field in your "image" collection
                        "$gte": formatted_start_date,
                        "$lte": formatted_end_date
                    }
                }
            },
            {
                "$lookup": {
                    "from": "defect",
                    "localField": "imageID",
                    "foreignField": "imageID",
                    "as": "defects"
                }
            },
            {
                "$lookup": {
                    "from": "batchImage",
                    "localField": "imageID",
                    "foreignField": "imageID",
                    "as": "batchInfo"
                }
            },
            {
                "$project": {
                        "_id": 0,
                        "imageID": 1,
                        "imagePath": 1,
                        "defects": {
                            "$map": {
                                "input": "$defects",
                                "as": "defect",
                                "in": {
                                    "outputLabel": "$$defect.outputLabel",  # Keep the outputLabel
                                    "bbox": "$$defect.bbox"  # Include the bbox field
                                }
                            }
                        },
                        "batchID": {
                            "$arrayElemAt": ["$batchInfo.batchID", 0]  # Assuming each imageID is linked to one batchID, extract the first batchID
                        }
                    }
            }
        ]
            
        

        else:
            pipeline = [
    {
        "$match": {
            "datetime": {
                "$gte": formatted_start_date,
                "$lte": formatted_end_date
            }
        }
    },
    {
        "$lookup": {
            "from": "defect",
            "localField": "imageID",
            "foreignField": "imageID",
            "as": "defects"
        }
    },
    {
        "$lookup": {
            "from": "batchImage",
            "localField": "imageID",
            "foreignField": "imageID",
            "as": "batchInfo"
        }
    },
    {
        "$addFields": {
            "hasRelevantDefect": {
                "$anyElementTrue": {
                    "$map": {
                        "input": "$defects",
                        "as": "defect",
                        "in": {"$in": ["$$defect.outputLabel", defectList]}
                    }
                }
            }
        }
    },
    {
        "$match": {
            "hasRelevantDefect": True
        }
    },
    {
        "$project": {
            "_id": 0,
            "imageID": 1,
            "imagePath": 1,
            "defects": {
                "$map": {
                    "input": "$defects",
                    "as": "defect",
                    "in": {
                        "outputLabel": "$$defect.outputLabel",
                        "bbox": "$$defect.bbox"
                    }
                }
            },
            "batchID": {
                "$arrayElemAt": ["$batchInfo.batchID", 0]
            },
        }
    }
]
        
    results = db.image.aggregate(pipeline)
    results_list = list(results) 
    print(results_list[start:end])  
    return jsonify(results_list[start:end])

@blueprint.route("/filter_editor_table", methods=['POST'])
def filter_editor_table(start=0, end=30):
    data = request.json
    startDate = data.get("startDate")
    endDate = data.get("endDate")
    defectList = data.get("defectList")
    return get_filtered_results(startDate, endDate, defectList, start, end)
    

@blueprint.route('/check_file_exists', methods=['GET'])
def check_file_exists():
    file_path = request.args.get('filePath', '')
    full_path = f'{root_dir}{file_path}'
    # print(full_path)
    exists = os.path.isfile(full_path)
    return jsonify({'exists': exists})

@blueprint.route('/load_more_images', methods=['POST'])
def load_more_images():
    data = request.json
    startindex = data.get("startindex")
    endindex = data.get("endindex")
    return update_editor_table(startindex, endindex)

@blueprint.route('/load_more_filtered_images', methods=['POST'])
def load_more_filtered_images():
    data = request.json
    startindex = data.get("startindex")
    endindex = data.get("endindex")
    startDate = data.get("startDate")
    endDate = data.get("endDate")
    defectList = data.get("defectList")
    return get_filtered_results(startDate, endDate, defectList, startindex, endindex)


@blueprint.route("/black", methods=["GET"])
def black():
    # return render_template(r"C:\Users\DanielYeoh\Desktop\INC-TSM-Phase3\black\templates\upload.html")
    # os.startfile(r"C:\Users\DanielYeoh\Desktop\INC-TSM-Phase3\black\app.py")
    return render_template("pages/b_result.html")
# END OF ANNOTATOR ROUTES
#####################################################################################################################################
# Team Black
from flask import (
    request,
    render_template,
    redirect,
    url_for,
    send_from_directory,
)
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
import uuid

def load_processed_videos():
        with open(Config.BLACK_PROCESSED_VIDEOS, "r") as file:
            return json.load(file)



def save_processed_videos(data):
    with open(Config.BLACK_PROCESSED_VIDEOS, "w") as file:
        json.dump(data, file, indent=4)



# @blueprint.route('/team_black_home', methods=['GET'])
# def team_black_home():
#     return render_template("pages/upload.html")

@blueprint.route('/team_black_home', methods=['GET'])
def team_black_home():
    processed_videos = load_processed_videos()
    print(len(processed_videos))
    processed_videos.reverse()  # Ensure latest uploads appear first
    return render_template("pages/upload.html", processed_videos=processed_videos)


# @blueprint.route('/team_black_upload', methods=['POST'])
# def team_black_upload():
#     if "file" not in request.files:
#         return redirect(url_for('blueprint.team_black_home'))
#     file = request.files["file"]
#     if file.filename == "":
#         return redirect(url_for('blueprint.team_black_home'))
#     if file:
#         unique_folder = str(uuid.uuid4())
#         output_dir = os.path.join(Config.BLACK_OUTPUT_FOLDER, unique_folder)
#         os.makedirs(output_dir, exist_ok=True)

#         filename = secure_filename(file.filename)
#         file_path = os.path.join(Config.BLACK_UPLOAD_FOLDER, filename)
#         file.save(file_path)

#         output_path = os.path.join(output_dir, f"output_{filename}")
#         tracker_path = Config.BLACK_TRACKER_WEIGHTS_FILE
#         processor = VideoProcessor(
#             seg_model_path=Config.BLACK_MARKING_MODEL_WEIGHTS_FILE,
#             det_model_path=Config.BLACK_SIGN_MODEL_WEIGHTS_FILE,
#         )
#         missing_signs = processor.process_video(
#             file_path, output_path, tracker_path
#         )

#         return render_template(
#             "pages/result.html",
#             output_video=f"{unique_folder}/output_{filename}",
#             missing_signs=missing_signs,
#             missing_count=len(missing_signs),
#         )

# @blueprint.route("static/outputs/<path:unique_folder>/<path:filename>")
# def serve_output(unique_folder, filename):
#     output_folder = os.path.join(Config.BLACK_OUTPUT_FOLDER, unique_folder)
#     return send_from_directory(
#         output_folder, filename, mimetype="video/mp4", conditional=True
#     )

# @app.route("/", methods=["GET", "POST"])
@blueprint.route("/team_black_upload", methods=["POST"])
def upload_video():
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        if file:
            folder = str(uuid.uuid4())

            output_dir = os.path.join(Config.BLACK_OUTPUT_FOLDER, folder)
            os.makedirs(output_dir, exist_ok=True)

            filename = secure_filename(file.filename)
            file_path = os.path.join(Config.BLACK_UPLOAD_FOLDER, filename)
            file.save(file_path)

            output_path = os.path.join(output_dir, f"output_{filename}")
            tracker_path = Config.BLACK_TRACKER_WEIGHTS_FILE
            marking_model_path = Config.BLACK_MARKING_MODEL_WEIGHTS_FILE
            sign_model_path = Config.BLACK_SIGN_MODEL_WEIGHTS_FILE

            processor = VideoProcessor(marking_model_path, sign_model_path)

            processor.process_video(file_path, output_path, tracker_path)

            missing_signs = processor.detect_missing_signs(output_path)

            missing_signs_data = {
                "number_of_missing_signs": len(missing_signs),
                "missing_signs_details": missing_signs,
            }

            json_path = os.path.join(output_dir, "missing_signs.json")
            with open(json_path, "w") as json_file:
                json.dump(missing_signs_data, json_file, indent=4)

            thumbnail_path = os.path.join(
                Config.BLACK_THUMBNAIL_FOLDER, f"{folder}.jpg"
            )
            processor.generate_thumbnail(file_path, thumbnail_path)

            processed_videos = load_processed_videos()

            processed_videos.append(
                {
                    "id": folder,
                    "filename": filename,
                    "output_path": output_path,
                    "thumbnail_url": os.path.join(Config.BLACK_THUMBNAIL_FOLDER, f"{folder}.jpg"),
                    "number_of_missing_signs": len(missing_signs),
                }
            )

            save_processed_videos(processed_videos)
            return redirect(url_for("home_blueprint.team_black_home"))



    # processed_videos = load_processed_videos()
    # processed_videos.reverse()
    # return render_template("pages/upload.html", processed_videos=processed_videos)

# @app.route("/result/<video_id>")
@blueprint.route("/team_black_result/<video_id>")
def result(video_id):
    processed_videos = load_processed_videos()

    video_data = next(
        (video for video in processed_videos if video["id"] == video_id), None
    )
    if not video_data:
        return "Video not found", 404

    json_path = os.path.join(
        Config.BLACK_OUTPUT_FOLDER, video_id, "missing_signs.json"
    )
    if not os.path.exists(json_path):
        return "Missing signs data not found", 404

    with open(json_path, "r") as json_file:
        missing_signs_data = json.load(json_file)

    for sign in missing_signs_data["missing_signs_details"]:
        sign["frame_path"] = url_for(
            "static",
            filename=f"outputs/{video_id}/marking_{sign['lane_marking_id']}_frame.jpg",
        )

    return render_template(
        "pages/result.html",
        video_data=video_data,
        missing_signs_data=missing_signs_data,
    )

VIDEO_FOLDER = r"C:\Users\DanielYeoh\Downloads\9251-traffic-1\team_black_y3s1\Video_To_Process"

@blueprint.route('/list-folder', methods=['GET'])
def list_folder():
    page = int(request.args.get('page', 1))
    items_per_page = int(request.args.get('items_per_page', 20))  # higher default for video files
    folder_name = request.args.get('folder')

    # If requesting files in a specific folder
    if folder_name:
        target_folder = os.path.join(VIDEO_FOLDER, folder_name)
        if not os.path.exists(target_folder):
            return jsonify({"error": "Folder not found"}), 404

        all_files = sorted([f for f in os.listdir(target_folder) if os.path.isfile(os.path.join(target_folder, f))])
        total_pages = (len(all_files) + items_per_page - 1) // items_per_page

        start = (page - 1) * items_per_page
        end = start + items_per_page
        paginated_files = all_files[start:end]

        return jsonify({
            "files": paginated_files,
            "page": page,
            "total_pages": total_pages
        })

    # Otherwise, return list of folders
    try:
        entries = os.listdir(VIDEO_FOLDER)
        folders = sorted([f for f in entries if os.path.isdir(os.path.join(VIDEO_FOLDER, f))])
        return jsonify({"folders": folders})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blueprint.route('/upload-folder', methods=['POST'])
def upload_folder():
    if 'folder' not in request.files:
        return jsonify({'error': 'No folder part'}), 400

    files = request.files.getlist('folder')
    if not files:
        return jsonify({'error': 'No files received'}), 400

    # Determine folder name from the first file's path
    first_file_path = files[0].filename
    folder_name = secure_filename(first_file_path.split('/')[0])  # 'FolderName/video1.mp4'

    upload_path = os.path.join(VIDEO_FOLDER, folder_name)
    os.makedirs(upload_path, exist_ok=True)

    for file in files:
        if file and allowed_file(file.filename):
            sub_path = '/'.join(file.filename.split('/')[1:])  # preserve subfolder structure (optional)
            file_save_path = os.path.join(upload_path, sub_path)
            os.makedirs(os.path.dirname(file_save_path), exist_ok=True)
            file.save(file_save_path)

    return jsonify({'message': 'Folder uploaded successfully'}), 200
@blueprint.route('/run-batch', methods=['POST'])
def run_batch():
    try:
        subprocess.Popen([
            r'C:\Users\DanielYeoh\Downloads\9251-traffic-1\team_black_y3s1\run_batch_processor.bat'
        ], shell=True)
        return jsonify({"message": "Batch processor started successfully."})
    except Exception as e:
        return jsonify({"message": f"Failed to run batch file: {e}"}), 500

@blueprint.route('/files/<folder>/<path:filename>')
def serve_batch_file(folder, filename):
    safe_folder = secure_filename(folder)
    full_folder_path = os.path.join(VIDEO_FOLDER, safe_folder)
    
    return send_from_directory(full_folder_path, filename)

REPORTS_DIR = r"C:\Users\DanielYeoh\Downloads\9251-traffic-1\team_black_y3s1\reports"

@blueprint.route("/list-reports")
def list_reports():
    folder = request.args.get("folder")
    page = int(request.args.get("page", 1))
    per_page = 10

    if folder:
        folder_path = os.path.join(REPORTS_DIR, folder)
        if not os.path.exists(folder_path):
            return jsonify({"error": "Folder not found"}), 404

        files = sorted(os.listdir(folder_path))
        total_pages = (len(files) + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        paginated_files = files[start:end]

        return jsonify({
            "folder": folder,
            "files": paginated_files,
            "page": page,
            "total_pages": total_pages,
        })

    else:
        folders = sorted([
            f for f in os.listdir(REPORTS_DIR)
            if os.path.isdir(os.path.join(REPORTS_DIR, f))
        ])
        return jsonify({"folders": folders})
@blueprint.route('/reports/<folder>/<path:filename>')
def serve_report_file(folder, filename):
    safe_folder = secure_filename(folder)
    report_folder = os.path.join(REPORTS_DIR, safe_folder)
    
    return send_from_directory(report_folder, filename, as_attachment=False)
