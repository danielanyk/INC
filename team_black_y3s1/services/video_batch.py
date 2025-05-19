import os
import uuid
import shutil
import cv2
import time
from collections import defaultdict
from services.video_processor import VideoProcessor, extract_gps_and_timestamp
from services.report_generator import ReportGenerator
from database.mongo_repository import MongoDB
from utils.onemap_service import reverse_geocode, generate_static_map
from services.engine_manager import EngineManager   
from utils.road_type_mapper import RoadTypeMapper
from config import Config
from datetime import datetime
from services.severity import SeverityEngine
# class VideoBatchProcessor:
#     def __init__(self, output_dir="reports"):
#         self.output_dir = output_dir
#         self.db = MongoDB()
#         self.report_generator = ReportGenerator()

#     def process_folder(self, folder_path):
#         collection_name = os.path.basename(folder_path)
#         video_report_dir = os.path.join(
#             self.output_dir, f"{collection_name}_{uuid.uuid4()}"
#         )
#         os.makedirs(video_report_dir, exist_ok=True)

#         for file_name in os.listdir(folder_path):
#             if not file_name.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
#                 continue

#             video_path = os.path.join(folder_path, file_name)
#             video_id = self.db.insert_video(file_name, collection_name)
#             print(f"[START] Processing video: {file_name}")

#             processor = VideoProcessor()
#             processor.process_video(video_path)
#             missing_records = processor.detect_missing_signs()

#             for defect in missing_records:
#                 defect_id = defect.get("defectId", str(uuid.uuid4()))

#                 try:
#                     self.db.insert_defect(
#                         video_id=video_id,
#                         defect_id=defect_id,
#                         defect_type_name=defect["defectType"],
#                         latitude=defect["latitude"],
#                         longitude=defect["longtitude"],
#                         severity=defect.get("severity", "Moderate"),
#                         image_path=defect["imagePath"],
#                     )
#                 except ValueError as e:
#                     print(f"[ERROR] {e}")
#                     continue

#                 address = reverse_geocode(defect["latitude"], defect["longtitude"])
#                 map_stream = generate_static_map(
#                     defect["latitude"], defect["longtitude"]
#                 )

#                 if address and map_stream:
#                     pdf_path = os.path.join(video_report_dir, f"{defect_id}.pdf")
#                     defect["DefectID"] = defect_id
#                     self.report_generator.generate_report(
#                         defect, address, map_stream, pdf_path
#                     )
#                     self.db.insert_report(defect_id)
#                 else:
#                     print(
#                         f"[WARN] Report skipped for defect {defect_id} (address/map unavailable)"
#                     )

#             self.db.update_video_status(video_id, "Completed")
#             print(f"[DONE] Finished processing video: {file_name}")

#         shutil.rmtree(folder_path, ignore_errors=True)
#         print(f"[INFO] Upload folder removed: {folder_path}")
#         print(f"[SUCCESS] Finished batch processing for folder: {collection_name}")
#         return collection_name

class VideoBatchProcessor:
    def __init__(self,db, output_dir="reports"):
        self.severity_engine = SeverityEngine()
        self.output_dir = output_dir
        self.db = db
        self.report_generator = ReportGenerator()
        self.engine_manager = EngineManager()  # Added EngineManager
        self.road_type_mapper = RoadTypeMapper(Config.ROAD_TYPE_MAPPER_PATH)

    def process_video(self, video_id, video_path, folder_name, video_report_dir, file_name):
        print(f"[START] Processing video: {file_name}")
        processor = VideoProcessor()
        processor.process_video(video_path)
        missing_records = processor.detect_missing_signs()
        print("Done black's part")

        # GPS & road type
        lat, lon, timestamp = extract_gps_and_timestamp(video_path)
        if lat is not None and lon is not None:
            road_type = self.road_type_mapper.get_road_type(lat, lon)
        else:
            lat, lon = 1.3521, 103.8198
            road_type = self.road_type_mapper.get_road_type(lat, lon)

        for record in missing_records:
            record["longtitude"] = lon
            record["latitude"] = lat
            record["roadType"] = road_type

        # Start reading video frames
        video_capture = cv2.VideoCapture(video_path)
        frame_idx = 0
        frame_interval = video_capture.get(cv2.CAP_PROP_FPS)

        engine_outputs = []
        image_map = {}  # new_img_path -> image_id
        images_collection = []

        while True:
            ret, frame = video_capture.read()
            if not ret:
                break
            frame_idx += 1

            if frame_idx % round(frame_interval) == 0:
                tmp_img_path = os.path.join(
                    "static/defect_imgs", f"{folder_name}_{video_id}_frame{frame_idx}.jpg"
                )
                cv2.imwrite(tmp_img_path, frame)

                for model_name in self.engine_manager.ENGINES:
                    result = self.engine_manager.predict(model_name, tmp_img_path)
                    if result is not None:
                        for lbl, box, conf, cid in zip(result["output_lbl"], result["xyxy"], result["confidence"], result["class_id"]):
                            if lbl.lower() in ["undamaged kerb", "no raveling"]:
                                continue
                            if isinstance(box, (list, tuple)) and len(box) == 4:
                                annotated_dict = annotate_image(tmp_img_path, [box], [lbl])
                                new_img_path = list(annotated_dict.values())[0]
                                try:
                                    cropped_path = crop_image(tmp_img_path, box)
                                    if os.path.exists(cropped_path):
                                        print("Cropped image exists right after saving.")
                                    else:
                                        print("Cropped image NOT found right after saving!")
                                    severity_start = time.time()
                                    print(cropped_path)
                                    severity = self.severity_engine.predict(cropped_path)
                                    print(f"[TIMER] Severity prediction took {time.time() - severity_start:.4f}s")
                                except Exception as e:
                                    print(f"[ERROR] Severity prediction failed: {e}")
                                    severity = "Unknown"
                                print(severity)
                                # Only add image entry once
                                if new_img_path not in image_map:
                                    image_id = str(uuid.uuid4())
                                    image_map[new_img_path] = image_id
                                    images_collection.append({
                                        "ImageID": image_id,
                                        "Path": new_img_path
                                    })

                                engine_outputs.append({
                                    "defectId": str(uuid.uuid4()),
                                    "defectType": lbl,
                                    "latitude": lat,
                                    "longtitude": lon,
                                    "imageId": image_map[new_img_path],
                                    "classId": cid,
                                    "roadType": road_type,
                                    "timestamp": timestamp,
                                    "severity": severity
                                })

        combined_records = missing_records + engine_outputs

        # Load DefectTypeID mappings
        defect_type_cache = {
            dt["DefectName"]: dt["DefectTypeID"]
            for dt in self.db.defect_types.find()
        }

        processed_defects = []
        processed_reports = []

        for defect in combined_records:
            defect_id = defect.get("defectId", str(uuid.uuid4()))
            defect_type_name = defect.get("defectType")
            defect_type_id = defect_type_cache.get(defect_type_name)

            if not defect_type_id:
                print(f"[ERROR] Unknown defect type: {defect_type_name}")
                continue

            address = reverse_geocode(defect["latitude"], defect["longtitude"])
            map_stream = generate_static_map(defect["latitude"], defect["longtitude"])
            if not (address and map_stream):
                print(f"[WARN] Skipped defect {defect_id}: address/map unavailable")
                continue

            pdf_path = os.path.join(video_report_dir, f"{defect_id}.pdf")
            defect["DefectID"] = defect_id
            self.report_generator.generate_report(defect, address, map_stream, pdf_path)
            processed_defects.append({
                "DefectID": defect_id,
                "VideoID": video_id,
                "DefectTypeID": defect_type_id,
                "Latitude": defect["latitude"],
                "Longitude": defect["longtitude"],
                "Severity": defect["longtitude"],
                "ImageID": defect.get("imageId"),  
                "DetectedDateTime": datetime.now().strftime("%d %b %Y, %H:%M:%S"),
            })

            processed_reports.append({
                "ReportID": str(uuid.uuid4()),
                "DefectID": defect_id,
                "RecommendationID": None,
                "RemarkId": None,
                "Status": "Unverified",
                "VerifiedAt": None,
                "latestmodificationtime": None,
                "generationtime": datetime.now().strftime("%d %b %Y, %H:%M:%S"),
                "reportpath": None,
                "tags": None,
                "measurement": None,
                "cause": None,
                "supervisorid": None,
                "via": None,
                "acknowledgement(check)": None,
                "inspectiontype(check)": None
            })

        self.db.batch_insert_images(images_collection)    
        self.db.batch_insert_defects(processed_defects)      
        self.db.batch_insert_reports(processed_reports)
        self.db.update_video_status(video_id, "Completed")

        print(f"[DONE] Finished processing video: {file_name}")
        video_capture.release()

        # shutil.rmtree(folder_path)
        # print(f"[INFO] Upload folder removed: {folder_path}")
        # print(f"[SUCCESS] Finished batch processing for folder: {collection_name}")
        # return collection_name
    
    def process_pending_videos(self, main_folder):
        pending_videos = list(self.db.videos.find({"ProcessingStatus": "Pending"}))

        if not pending_videos:
            print("[INFO] No pending videos to process.")
            return

        print(f"[INFO] Found {len(pending_videos)} pending videos to process.")

        for video in pending_videos:
            video_path = os.path.join(main_folder, video["FolderName"], video["VideoName"])  # Adjust base path!
            if not os.path.exists(video_path):
                print(f"[WARN] Video file missing: {video_path}")
                self.db.update_video_status(video["VideoID"], "Removed")
                continue

            video_report_dir = os.path.join(self.output_dir, f"{video['FolderName']}")
            os.makedirs(video_report_dir, exist_ok=True)

            self.process_video(video["VideoID"], video_path, video["FolderName"], video_report_dir,video["VideoName"])

    def process_folder(self, folder_path):
        collection_name = os.path.basename(folder_path)
        parts = collection_name.split("_")
        if len(parts) < 2:
            print("[ERROR] Invalid folder name format. Expected 'Firstname_Lastname_Date'")
            return

        firstname = parts[0]
        lastname = parts[1]

        if not self.db.user_exists_by_name(firstname, lastname):
            print(f"[ERROR] User {firstname} {lastname} does not exist. Folder will not be processed.")
            return

        self.insert_videos_from_folder(folder_path)
        print(f"[INFO] Inserted all videos in folder: {folder_path}")
    
    def insert_videos_from_folder(self, folder_path):
        collection_name = os.path.basename(folder_path)

        for file_name in os.listdir(folder_path):
            if not file_name.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
                continue

            video_path = os.path.join(folder_path, file_name)

            # Check if already inserted (prevent duplicate)
            existing = self.db.videos.find_one({"VideoName": file_name, "FolderName": collection_name})
            if existing:
                print(f"[INFO] Video {file_name} already exists in DB, skipping insert.")
                continue

            video_id = self.db.insert_video(file_name, collection_name)
            print(f"[INFO] Inserted video metadata: {file_name} (ID: {video_id})")

def annotate_image(image_path, boxes, labels, normalized=None):
    """
    Annotate image with all boxes per class, saving one image per class type.

    Parameters:
    - image_path: Path to original frame.
    - boxes: List of bounding boxes.
    - labels: List of defect labels corresponding to each box.
    - normalized: Optional override. If None, auto-detects.

    Returns:
    - Dictionary of label -> saved image path.
    """
    img = cv2.imread(image_path)
    height, width = img.shape[:2]

    # Auto-detect normalization if not specified
    if normalized is None:
        normalized = is_normalized_box(boxes)

    # Group boxes by label
    boxes_by_label = defaultdict(list)
    for box, label in zip(boxes, labels):
        if isinstance(box, (list, tuple)) and len(box) == 4:
            boxes_by_label[label].append(box)

    output_paths = {}

    for label, label_boxes in boxes_by_label.items():
        img_copy = img.copy()
        for box in label_boxes:
            x1, y1, x2, y2 = box
            if normalized:
                x1 = int(x1 * width)
                y1 = int(y1 * height)
                x2 = int(x2 * width)
                y2 = int(y2 * height)
            else:
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

            cv2.rectangle(img_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img_copy, label, (x1, max(y1 - 10, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Save with label name in filename
        label_safe = label.replace(" ", "_").lower()
        out_path = image_path.replace(".jpg", f"_{label_safe}.jpg")
        cv2.imwrite(out_path, img_copy)
        output_paths[label] = out_path

    return output_paths

    return output_paths
def is_normalized_box(boxes):
    """Return True if all coordinates are between 0 and 1."""
    return all(0.0 <= x <= 1.0 for box in boxes for x in box)
def crop_image(image_path, bbox, identifier=None):
    print(f"[INFO] Cropping image: {image_path}")
    
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    h, w = image.shape[:2]
    print(f"[INFO] Original image size: width={w}, height={h}")
    print(f"[INFO] Received bbox: {bbox}")

    # Convert to normalized if not already
    if not is_normalized_box([bbox]):
        print("[INFO] BBox not normalized. Converting to normalized format.")
        x_min = bbox[0] / w
        y_min = bbox[1] / h
        x_max = bbox[2] / w
        y_max = bbox[3] / h
        bbox = [x_min, y_min, x_max, y_max]
    else:
        print("[INFO] BBox is already normalized.")

    # Now scale to absolute pixel coordinates
    x_min = int(bbox[0] * w)
    y_min = int(bbox[1] * h)
    x_max = int(bbox[2] * w)
    y_max = int(bbox[3] * h)
    print(f"[INFO] Cropping area in pixels: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")

    if x_max <= x_min or y_max <= y_min:
        print("[WARNING] Invalid crop dimensions (zero or negative size). Skipping crop.")
        return None

    cropped_image = image[y_min:y_max, x_min:x_max]
    print(f"[INFO] Cropped image shape: {cropped_image.shape}")

    if cropped_image.size == 0:
        print("[ERROR] Cropped image is empty. Skipping save.")
        return None

    original_image_name, extension = os.path.splitext(os.path.basename(image_path))
    cropped_image_name = (
        f"{original_image_name}_cropped_{identifier}{extension}" if identifier else
        f"{original_image_name}_cropped{extension}"
    )
    save_dir = os.path.dirname(image_path)
    cropped_image_path = os.path.join(save_dir, cropped_image_name)
    print(f"[INFO] Saving cropped image to: {cropped_image_path}")

    success = cv2.imwrite(cropped_image_path, cropped_image)
    if not success:
        print("[ERROR] cv2.imwrite() failed to write the cropped image.")
        return None

    print("[INFO] Cropped image saved successfully.")
    return cropped_image_path
