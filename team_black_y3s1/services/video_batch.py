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
    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        self.db = MongoDB()
        self.report_generator = ReportGenerator()
        self.engine_manager = EngineManager()  # Added EngineManager
        self.road_type_mapper = RoadTypeMapper(Config.ROAD_TYPE_MAPPER_PATH)

    def process_folder(self, folder_path):
        collection_name = os.path.basename(folder_path)
        video_report_dir = os.path.join(
            self.output_dir, f"{collection_name}_{uuid.uuid4()}"
        )
        os.makedirs(video_report_dir, exist_ok=True)

        for file_name in os.listdir(folder_path):
            if not file_name.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
                continue

            video_path = os.path.join(folder_path, file_name)
            video_id = self.db.insert_video(file_name, collection_name)
            print(f"[START] Processing video: {file_name}")

            processor = VideoProcessor()
            processor.process_video(video_path)
            missing_records = processor.detect_missing_signs()
            print("Done black's part")

            # Extract GPS and timestamp for current video
            lat, lon, timestamp = extract_gps_and_timestamp(video_path)
            

            if lat is not None and lon is not None:
                road_type = self.road_type_mapper.get_road_type(lat, lon)
            else:
                # Default to central Singapore
                lat, lon = 1.3521, 103.8198
                road_type = self.road_type_mapper.get_road_type(lat, lon)  # No GPS needed here
            for record in missing_records:
                record["longtitude"] = lon
                record["latitude"] = lat
                record["roadType"] = road_type

            video_capture = cv2.VideoCapture(video_path)
            engine_outputs = []
            frame_idx = 0
            frame_interval=video_capture.get(cv2.CAP_PROP_FPS)
            generated_images=[]
            while True:
                ret, frame = video_capture.read()
                if not ret:
                    break
                frame_idx += 1
                # save a temporary image for EngineManager to consume
                if frame_idx % round(frame_interval) == 0:
                    tmp_img_path = os.path.join(
                        "static/defect_imgs",
                        f"{collection_name}_{video_id}_frame{frame_idx}.jpg"
                    )
                    cv2.imwrite(tmp_img_path, frame)
                    generated_images.append(tmp_img_path)
                                    # run through each engine
                    frame_start_time = time.time()
                    for model_name in self.engine_manager.ENGINES:
                        # try:
                            # Capture time for each model prediction
                            model_start_time = time.time()
                            
                            result = self.engine_manager.predict(model_name, tmp_img_path)
                            
                            # For each result, append output to engine_outputs
                            if result is not None:
                                for lbl, box, conf, cid in zip(result["output_lbl"], result["xyxy"], result["confidence"], result["class_id"]):
                                    if lbl.lower() == "undamaged kerb" or lbl.lower() == "no raveling":
                                        continue  # Skip this label (as per your previous condition)

                                    if isinstance(box, (list, tuple)) and len(box) == 4:
                                        # Annotate the image with only one defect type

                                        annotated_dict = annotate_image(tmp_img_path, [box], [lbl])
                                        new_img_path = list(annotated_dict.values())[0]  # Wrap box in a list to pass to the function
                                        
                                        # Store the updated image path in the records
                                        engine_outputs.append({
                                            "defectId": str(uuid.uuid4()),
                                            "defectType": lbl,
                                            "latitude": lat,
                                            "longtitude": lon,
                                            "imagePath": new_img_path,  # Use the new image path with defect type in the name
                                            "classId": cid,
                                            "roadType": road_type,
                                            "timestamp": timestamp
                                        })
                                    else:
                                        print(f"[WARN] Invalid box format: {box}. Skipping annotation.")
                            
                            # Capture the end time for each model and print the time taken
                            model_end_time = time.time()
                            model_duration = model_end_time - model_start_time
                            print(f"[INFO] Model '{model_name}' processed in {model_duration:.2f} seconds.")
                        
                        # except Exception as e:
                        #     print(f"[ERROR] Engine '{model_name}' on frame {frame_idx}: {e}")

                    # After processing all models, capture the total frame time
                    frame_end_time = time.time()
                    frame_duration = frame_end_time - frame_start_time

                    # Print the time taken for the entire frame processing
                    print(f"[INFO] Total time for frame {frame_idx}: {frame_duration:.2f} seconds.")


            print("missing_records:",missing_records)
            print("engine_outputs:",engine_outputs)
            combined_records = missing_records + engine_outputs
            for img_path in generated_images:
                try:
                    os.remove(img_path)
                except Exception as e:
                    print(f"[WARN] Could not delete image {img_path}: {e}")

            for defect in combined_records:
                defect_id = defect.get("defectId", str(uuid.uuid4()))

                try:
                    image_id = self.db.insert_defect_image(defect["imagePath"])

                    self.db.insert_defect(
                        video_id=video_id,
                        defect_id=defect_id,
                        defect_type_name=defect["defectType"],
                        latitude=defect["latitude"],
                        longitude=defect["longtitude"],
                        severity=defect.get("severity", "Moderate"),
                        image_id=image_id,
                    )
                except ValueError as e:
                    print(f"[ERROR] {e}")
                    continue

                address = reverse_geocode(defect["latitude"], defect["longtitude"])
                map_stream = generate_static_map(
                    defect["latitude"], defect["longtitude"]
                )

                if address and map_stream:
                    pdf_path = os.path.join(video_report_dir, f"{defect_id}.pdf")
                    defect["DefectID"] = defect_id
                    self.report_generator.generate_report(
                        defect, address, map_stream, pdf_path
                    )
                    self.db.insert_report(defect_id)
                else:
                    print(
                        f"[WARN] Report skipped for defect {defect_id} (address/map unavailable)"
                    )

            self.db.update_video_status(video_id, "Completed")
            print(f"[DONE] Finished processing video: {file_name}")
        video_capture.release()
        shutil.rmtree(folder_path)
        print(f"[INFO] Upload folder removed: {folder_path}")
        print(f"[SUCCESS] Finished batch processing for folder: {collection_name}")
        return collection_name
    
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