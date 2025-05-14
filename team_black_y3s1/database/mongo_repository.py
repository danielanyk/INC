import json
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import uuid

MONGO_URI = "mongodb://localhost:27018/"
DB_NAME = "defect_db"

with open("database/default_data.json", "r") as f:
    default_data = json.load(f)

DEFAULT_ROLES = default_data["roles"]
DEFAULT_USERS = default_data["users"]
DEFAULT_DEFECT_TYPES = default_data["defect_types"]


class MongoDB:
    def __init__(self, uri=MONGO_URI, db_name=DB_NAME, initialize_data=True):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None

        self.users = None
        self.user_details=None
        self.roles = None
        self.videos = None
        self.defects = None
        self.defect_types = None
        self.reports = None
        self.images=None
        self.remarks=None
        self.recommendations=None
        self.images=None

        self._connect()
        if initialize_data:
            self._initialize_roles_and_users()
            self._initialize_defect_types()

    def _connect(self):
        if self.client is None:
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
                self.client.admin.command("ping")
                self.db = self.client[self.db_name]

                self.users = self.db["users"]
                self.roles = self.db["roles"]
                self.videos = self.db["videos"]
                self.defects = self.db["defects"]
                self.defect_types = self.db["defect_types"]
                self.reports = self.db["reports"]
                self.images = self.db["images"]

                print("[INFO] MongoDB connected successfully")
            except ConnectionFailure as e:
                print(f"[ERROR] MongoDB connection failed: {e}")
                raise

    def _initialize_roles_and_users(self):
        self.roles.delete_many({})
        self.roles.insert_many(DEFAULT_ROLES)

        self.users.delete_many({})
        self.users.insert_many(DEFAULT_USERS)

        print("[INFO] Default roles and users initialized")

    def _initialize_defect_types(self):
        self.defect_types.delete_many({})
        self.defect_types.insert_many(DEFAULT_DEFECT_TYPES)

        print("[INFO] Default defect types initialized")

    def insert_defect_image(self, image_path):
        # Check if image already exists
        existing = self.images.find_one({"ImagePath": image_path})
        if existing:
            return existing["_id"]

        image_id = str(uuid.uuid4())
        self.images.insert_one({
            "_id": image_id,
            "ImagePath": image_path
        })
        print(f"[INFO] Inserted new image record for {image_path}")
        return image_id


    def insert_defect(
        self,
        video_id,
        defect_id,
        defect_type_name,
        latitude,
        longitude,
        severity,
        image_id,
    ):
        if not video_id or not defect_id or not defect_type_name:
            print("[ERROR] Missing required fields in insert_defect")
            return None

        defect_type = self.defect_types.find_one({"DefectName": defect_type_name})
        if not defect_type:
            print(f"[ERROR] Unknown defect type: {defect_type_name}")
            return None

        defect_data = {
            "DefectID": defect_id,
            "VideoID": video_id,
            "DefectTypeID": defect_type["DefectTypeID"],
            "Latitude": latitude,
            "Longitude": longitude,
            "Severity": severity,
            "ImageID": image_id,
            "DetectedDateTime": datetime.now().strftime("%d %b %Y, %H:%M:%S"),
        }

        self.defects.insert_one(defect_data)
        print(f"[INFO] Inserted defect {defect_id}")
        return defect_id


    def insert_video(self, video_name, folder_name, user_id=1):
        video_data = {
            "VideoID": str(uuid.uuid4()),
            "UserID": user_id,
            "ProcessingStatus": "Pending",
            "FolderName": folder_name,
            "UploadDatetime": datetime.now().strftime("%d %b %Y, %H:%M:%S"),
            "VideoName": video_name,
        }

        self.videos.insert_one(video_data)
        print(f"[INFO] Insert video '{video_name}' with ID {video_data['VideoID']}")
        return video_data["VideoID"]

    def insert_report(self, defect_id):
        if not defect_id:
            print("[ERROR] Missing defect_id in insert_report")
            return None

        report_data = {
            "ReportID": str(uuid.uuid4()),
            "DefectID": defect_id,
            "RecommendationID":None,
            "RemarkId":None,
            "Status": "Unverified",
            "VerifiedAt": None,
            "latestmodificationtime":None,
            "generationtime": None,
            "reportpath":None,
            "tags":None,
            "measurement":None,
            "cause":None,
            "supervisorid":None,
            "via":None,
            "acknowledgement(check)":None,
            "inspectiontype(check)":None
        }

        self.reports.insert_one(report_data)
        print(f"[INFO] Insert report for DefectID: {defect_id}")
        return report_data["ReportID"]

    def update_video_status(self, video_id, status):
        result = self.videos.update_one(
            {"VideoID": video_id}, {"$set": {"ProcessingStatus": status}}
        )
        if result.modified_count > 0:
            print(f"[INFO] Updated video {video_id} status to '{status}'")
        else:
            print(f"[WARN] No update made for VideoID: {video_id}")

    def get_defect_by_id(self, defect_id):
        return self.defects.find_one({"DefectID": defect_id})

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            print("[INFO] MongoDB connection closed")

    def ping(self):
        try:
            self.client.admin.command("ping")
            print("[INFO] MongoDB ping successful")
        except Exception as e:
            print(f"[WARN] MongoDB ping failed: {e}")
            self.close()
