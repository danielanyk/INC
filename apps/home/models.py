from apps import mongo
from bson.objectid import ObjectId
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db=mongo.db
class Product:

    @staticmethod
    def find_by_id(_id):
        return db.products.find_one({'_id': _id})

    @staticmethod
    def get_list():
        db=mongo.db
        print(db)
        return list(db.products.find())

    @staticmethod
    def to_dict(product):
        return {
            'id': str(product['_id']),
            'name': product['name'],
            'info': product['info'],
            'price': product['price']
        }

    @staticmethod
    def get_json_list():
        products = Product.get_list()
        return [Product.to_dict(product) for product in products]


class StatusChoices:
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    RUNNING = 'RUNNING'

class User(UserMixin):
    def __init__(self, user_id, username, password_hash=None):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)

    @classmethod
    def get(cls, user_id):
        user_data = db.users.find_one({"_id": ObjectId(user_id)})
        if not user_data:
            return None
        return cls(str(user_data["_id"]), user_data["username"], user_data["password"])

    @classmethod
    def find_by_username(cls, username):
        user_data = db.users.find_one({"username": username})
        if not user_data:
            return None
        return cls(str(user_data["_id"]), user_data["username"], user_data["password"])

    def get_id(self):
        return self.user_id

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    def save_to_mongo(self):
        if not self.password_hash:
            raise ValueError("Password hash missing")
        db.users.insert_one({
            "username": self.username,
            "password": self.password_hash
        })


class TaskResult:

    @staticmethod
    def find_by_id(_id):
        return db.task_results.find_one({'_id': ObjectId(_id)})

    @staticmethod
    def get_list():
        return list(db.task_results.find())

    @staticmethod
    def to_dict(task_result):
        return {
            'id': str(task_result['_id']),
            'task_name': task_result['task_name'],
            'periodic_task_name': task_result['periodic_task_name'],
            'status': task_result['status'],
            'result': task_result['result'],
            'date_created': task_result['date_created'],
            'date_done': task_result['date_done']
        }

    @staticmethod
    def get_json_list():
        task_results = TaskResult.get_list()
        return [TaskResult.to_dict(task_result) for task_result in task_results]

    @staticmethod
    def get_latest():
        try:
            # Attempt to retrieve the first document from the cursor; use `next` to avoid IndexError
            latest_task_result = next(db.task_results.find().sort('_id', -1).limit(1), None)
            if latest_task_result:
                return TaskResult.to_dict(latest_task_result)
            else:
                return None  # Return None or an appropriate response if no document is found
        except Exception as e:
            # Log the exception or handle it as needed
            print(f"An error occurred: {e}")
            return None

    @staticmethod
    def get_all():
        return list(db.task_results.find())
    


    
# Team Black's model
from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    send_from_directory,
)
from werkzeug.utils import secure_filename
import os
import cv2
from ultralytics import YOLO
import torch
import numpy as np



# class VideoProcessor:
#     def __init__(self, seg_model_path, det_model_path):
#         self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
#         self.seg_model = YOLO(seg_model_path).to(self.device)
#         print(self.device)
#         self.det_model = YOLO(det_model_path).to(self.device)
#         self.marking = {1: "Crosswalk", 3: "Stop Line"}
#         self.sign = {0: "Pedestrian Crossing", 1: "Stop Sign"}
#         self.pair = {self.marking[1]: self.sign[0], self.marking[3]: self.sign[1]}
#         self.marking_dict = {}
#         self.sign_dict = {}
#         self.first_frames = {}  # Store the first frame paths of missing markings

#     def process_video(self, video_path, output_path, tracker_path):
#         cap = cv2.VideoCapture(video_path)
#         fps = int(cap.get(cv2.CAP_PROP_FPS))
#         width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#         height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#         fourcc = cv2.VideoWriter_fourcc(*"avc1")
#         out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
#         frame_count = 0

#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             def mask(frame):
#                 height, width = frame.shape[:2]
#                 mask = np.zeros_like(frame)

#                 vertices = np.array(
#                     [
#                         [
#                             (0, height),
#                             (0, height // 1.5),
#                             (width, height // 1.5),
#                             (width, height),
#                         ]
#                     ],
#                     dtype=np.int32,
#                 )

#                 cv2.fillPoly(mask, vertices, (255, 255, 255))
#                 return cv2.bitwise_and(frame, mask)

#             seg_results = self.seg_model.track(
#                 mask(frame),
#                 device=self.device,
#                 verbose=False,
#                 tracker=tracker_path,
#                 persist=True,
#                 conf=0.6,
#                 classes=[1, 3],
#             )
#             det_results = self.det_model.track(
#                 frame,
#                 device=self.device,
#                 verbose=False,
#                 tracker=tracker_path,
#                 persist=True,
#                 conf=0.6,
#             )

#             self.update_dict(seg_results, self.marking_dict, self.marking, frame_count)
#             self.update_dict(det_results, self.sign_dict, self.sign, frame_count)

#             seg_frame = seg_results[0].plot(line_width=2)
#             det_frame = det_results[0].plot(line_width=2)
#             combined_frame = cv2.addWeighted(seg_frame, 0.5, det_frame, 0.5, 0)
#             out.write(combined_frame)

#             frame_count += 1

#         cap.release()
#         out.release()
#         return self.detect_missing_signs(output_path)

#     def update_dict(self, results, target_dict, label_map, frame_count):
#         for box in results[0].boxes:
#             if box.id is not None:
#                 obj_type = label_map[box.cls.item()]
#                 obj_id = box.id.item()
#                 if obj_type not in target_dict:
#                     target_dict[obj_type] = {}
#                 if obj_id not in target_dict[obj_type]:
#                     target_dict[obj_type][obj_id] = [frame_count, frame_count]
#                 else:
#                     target_dict[obj_type][obj_id][1] = frame_count

#     def detect_missing_signs(self, output_path):
#         missing_signs = []

#         for marking_type, markings in self.marking_dict.items():
#             paired_sign_type = self.pair.get(marking_type)
#             if not paired_sign_type or paired_sign_type not in self.sign_dict:
#                 for marking_id, marking_frames in markings.items():
#                     start_frame = marking_frames[0]
#                     first_frame_path = os.path.join(
#                         os.path.dirname(output_path),
#                         f"marking_{marking_id}_frame.jpg",
#                     )

#                     # Save the first frame
#                     if marking_id not in self.first_frames:
#                         self.save_frame(output_path, start_frame, first_frame_path)
#                         self.first_frames[marking_id] = first_frame_path

#                     missing_signs.append(
#                         {
#                             "lane_marking_id": marking_id,
#                             "marking_type": marking_type,
#                             "frame_range": marking_frames,
#                             "missing_sign_type": paired_sign_type,
#                             "frame_path": first_frame_path,
#                         }
#                     )
#             continue
#         return missing_signs

#     def save_frame(self, video_path, frame_index, save_path):
#         """Save a specific frame from a video."""
#         cap = cv2.VideoCapture(video_path)
#         cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
#         ret, frame = cap.read()
#         if ret:
#             cv2.imwrite(save_path, frame)
#         cap.release()

# -----------------------
# from flask import (
#     Flask,
#     request,
#     jsonify,
#     render_template,
#     redirect,
#     send_from_directory,
#     url_for,
# )

# from flask_cors import CORS
# from werkzeug.utils import secure_filename
# import os
# import cv2
# import numpy as np
# import torch
# import uuid
# import json
# from ultralytics import YOLO

# app = Flask(__name__)
# app.secret_key = "inc"

# app.config["UPLOAD_FOLDER"] = "uploads"
# app.config["OUTPUT_FOLDER"] = "static/outputs"
# app.config["THUMBNAIL_FOLDER"] = "static/thumbnails"

# os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
# os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)
# os.makedirs(app.config["THUMBNAIL_FOLDER"], exist_ok=True)


class VideoProcessor:
    def __init__(self, marking_model_path, sign_model_path):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.marking_model = YOLO(marking_model_path).to(self.device)
        self.sign_model = YOLO(sign_model_path).to(self.device)
        self.marking = {1: "Crosswalk", 3: "Stop Line"}
        self.sign = {0: "Pedestrian Crossing", 1: "Stop Sign"}
        self.pair = {self.marking[1]: self.sign[0], self.marking[3]: self.sign[1]}
        self.marking_dict = {}
        self.sign_dict = {}
        self.first_frames = {}

    def process_video(self, video_path, output_path, tracker_path):
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            masked_frame = self.mask(frame)
            marking_results = self.marking_model.track(
                masked_frame,
                device=self.device,
                verbose=False,
                tracker=tracker_path,
                persist=True,
                conf=0.6,
                classes=[1, 3],
            )
            sign_results = self.sign_model.track(
                frame,
                device=self.device,
                verbose=False,
                tracker=tracker_path,
                persist=True,
                conf=0.6,
            )
            self.update_dict(
                marking_results, self.marking_dict, self.marking, frame_count
            )
            self.update_dict(sign_results, self.sign_dict, self.sign, frame_count)

            self.draw_detections(frame, marking_results, self.marking)
            self.draw_detections(frame, sign_results, self.sign)

            out.write(frame)
            frame_count += 1

        cap.release()
        out.release()

    def mask(self, frame):
        height, width = frame.shape[:2]
        mask = np.zeros_like(frame)
        vertices = np.array(
            [
                [
                    (0, height),
                    (0, height // 1.5),
                    (width, height // 1.5),
                    (width, height),
                ]
            ],
            dtype=np.int32,
        )
        cv2.fillPoly(mask, vertices, (255, 255, 255))
        masked_frame = cv2.bitwise_and(frame, mask)
        return masked_frame

    def update_dict(self, results, target_dict, label_map, frame_count):
        for box in results[0].boxes:
            if box.id is not None:
                obj_type = label_map[box.cls.item()]
                obj_id = box.id.item()
                if obj_type not in target_dict:
                    target_dict[obj_type] = {}
                if obj_id not in target_dict[obj_type]:
                    target_dict[obj_type][obj_id] = [frame_count, frame_count]
                else:
                    target_dict[obj_type][obj_id][1] = frame_count

    def draw_detections(self, frame, results, label_map):
        color_map = {
            "Crosswalk": (0, 255, 0),
            "Stop Line": (255, 0, 0),
            "Pedestrian Crossing": (0, 0, 255),
            "Stop Sign": (0, 0, 0),
        }

        for box in results[0].boxes:
            if box.id is not None:
                obj_type = label_map[box.cls.item()]
                obj_id = int(box.id.item())
                confidence = box.conf.item()
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = color_map.get(obj_type, (0, 255, 0))
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"ID:{obj_id} {obj_type} {confidence:.2f}"
                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    color,
                    3,
                )

    def detect_missing_signs(self, output_path):
        missing_signs = []
        for marking_type, markings in self.marking_dict.items():
            paired_sign_type = self.pair.get(marking_type)
            if not paired_sign_type or paired_sign_type not in self.sign_dict:
                for marking_id, marking_frames in markings.items():
                    start_frame = marking_frames[0]
                    first_frame_path = os.path.join(
                        os.path.dirname(output_path),
                        f"marking_{marking_id}_frame.jpg",
                    )
                    if marking_id not in self.first_frames:
                        self.save_frame(output_path, start_frame, first_frame_path)
                        self.first_frames[marking_id] = first_frame_path
                    missing_signs.append(
                        {
                            "lane_marking_id": marking_id,
                            "marking_type": marking_type,
                            "frame_range": marking_frames,
                            "missing_sign_type": paired_sign_type,
                            "frame_path": first_frame_path,
                        }
                    )
        return missing_signs

    def save_frame(self, video_path, frame_index, save_path):
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(save_path, frame)
        cap.release()

    def generate_thumbnail(self, video_path, thumbnail_path):
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(thumbnail_path, frame)
        cap.release()


# def clear_processed_videos():
#     with open("processed_videos.json", "w") as file:
#         json.dump([], file, indent=4)


# def load_processed_videos():
#     if os.path.exists("processed_videos.json"):
#         with open("processed_videos.json", "r") as file:
#             return json.load(file)
#     return []


# def save_processed_videos(data):
#     with open("processed_videos.json", "w") as file:
#         json.dump(data, file, indent=4)


