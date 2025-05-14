import os
import cv2
import torch
import numpy as np
from datetime import datetime
from ultralytics import YOLO
from config import Config
from utils.road_type_mapper import RoadTypeMapper
import uuid


# class VideoProcessor:
#     def __init__(self):
#         self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
#         self.model = YOLO(Config.COMBINED_MODEL_PATH).to(self.device)
#         self.road_type_mapper = RoadTypeMapper(Config.ROAD_TYPE_MAPPER_PATH)

#         self.marking_classes = {
#             0: "Keep Left Divider Context",
#             2: "Pedestrian Crosswalk Context",
#             4: "Stop Line Context",
#         }

#         self.sign_classes = {
#             1: "Keep Left Sign",
#             3: "Pedestrian Crossing Sign",
#             5: "Stop Sign",
#         }

#         self.expected_pairs = {
#             self.marking_classes[0]: self.sign_classes[1],
#             self.marking_classes[2]: self.sign_classes[3],
#             self.marking_classes[4]: self.sign_classes[5],
#         }

#         self.marking_tracks = {}
#         self.sign_tracks = {}
#         self.total_frames = 1
#         self.current_frame_index = 0
#         self.video_path = None

#     def process_video(self, video_path, tracker_path=Config.TRACKER_MODEL_PATH):
#         self.video_path = video_path
#         self.current_frame_index = 0

#         video_capture = cv2.VideoCapture(video_path)
#         self.total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

#         while True:
#             ret, frame = video_capture.read()
#             if not ret:
#                 break

#             detection_results = self.model.track(
#                 frame,
#                 device=self.device,
#                 tracker=tracker_path,
#                 conf=0.5,
#                 persist=True,
#                 verbose=False,
#             )

#             self._update_tracking_data(detection_results)
#             self.current_frame_index += 1

#         video_capture.release()

#     def detect_missing_signs(self, fps=60):
#         missing_defects = []
#         search_margin_frames = fps * 3
#         video_capture = cv2.VideoCapture(self.video_path)

#         for marking_label, tracked_ids in self.marking_tracks.items():
#             expected_sign = self.expected_pairs.get(marking_label)
#             if not expected_sign:
#                 continue

#             intervals = list(tracked_ids.values())
#             merged_intervals = self._merge_intervals(intervals)

#             for start_frame, end_frame in merged_intervals:
#                 lower_bound = max(0, start_frame - search_margin_frames)
#                 upper_bound = end_frame + search_margin_frames

#                 found = any(
#                     s_start <= upper_bound and s_end >= lower_bound
#                     for s_start, s_end in self.sign_tracks.get(
#                         expected_sign, {}
#                     ).values()
#                 )

#                 if not found:
#                     video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
#                     ret, frame = video_capture.read()
#                     if not ret:
#                         continue

#                     masked_frame = self._apply_mask(frame)
#                     predictions = self.model.predict(
#                         masked_frame,
#                         device=self.device,
#                         conf=0.5,
#                         verbose=False,
#                     )

#                     annotated_frame = self._annotate_frame(
#                         frame, predictions, marking_label
#                     )

#                     defect_id = str(uuid.uuid4())
#                     timestamp = datetime.now().strftime("%d %b %Y, %H:%M:%S")
#                     image_path = os.path.join(
#                         Config.DEFECT_IMGS_FOLDER, f"{defect_id}.jpg"
#                     )
#                     cv2.imwrite(image_path, annotated_frame)

#                     #! Placeholder coordinates for defect location
#                     lat, lon = 1.3441883512097617, 103.74960618214755

#                     defect_info = {
#                         "videoId": os.path.basename(self.video_path),
#                         "defectId": defect_id,
#                         "defectType": f"Missing Signage ({expected_sign})",
#                         "severity": None,
#                         "latitude": lat,
#                         "longtitude": lon,
#                         "timestamp": timestamp,
#                         "imagePath": image_path,
#                     }
#                     road_type = self.road_type_mapper.get_road_type(lat, lon)
#                     defect_info["roadType"] = road_type
#                     missing_defects.append(defect_info)

#         video_capture.release()
#         return missing_defects

#     def _merge_intervals(self, intervals, margin=10):
#         if not intervals:
#             return []
#         intervals.sort()
#         merged = [intervals[0]]
#         for current in intervals[1:]:
#             previous = merged[-1]
#             if previous[1] + margin >= current[0]:
#                 previous[1] = max(previous[1], current[1])
#             else:
#                 merged.append(current)
#         return merged

#     def _apply_mask(self, frame):
#         height, width = frame.shape[:2]
#         mask = np.zeros_like(frame)
#         vertices = np.array(
#             [
#                 [
#                     (0, height),
#                     (0, int(height / 1.5)),
#                     (width, int(height / 1.5)),
#                     (width, height),
#                 ]
#             ],
#             dtype=np.int32,
#         )
#         cv2.fillPoly(mask, vertices, (255, 255, 255))
#         return cv2.bitwise_and(frame, mask)

#     def _update_tracking_data(self, results):
#         for box in results[0].boxes:
#             if box.id is None:
#                 continue
#             class_id = int(box.cls.item())
#             track_id = f"{class_id}_{int(box.id.item())}"

#             if class_id in self.marking_classes:
#                 label = self.marking_classes[class_id]
#                 if label not in self.marking_tracks:
#                     self.marking_tracks[label] = {}
#                 if track_id not in self.marking_tracks[label]:
#                     self.marking_tracks[label][track_id] = [
#                         self.current_frame_index,
#                         self.current_frame_index,
#                     ]
#                 else:
#                     self.marking_tracks[label][track_id][1] = self.current_frame_index

#             elif class_id in self.sign_classes:
#                 label = self.sign_classes[class_id]
#                 if label not in self.sign_tracks:
#                     self.sign_tracks[label] = {}
#                 if track_id not in self.sign_tracks[label]:
#                     self.sign_tracks[label][track_id] = [
#                         self.current_frame_index,
#                         self.current_frame_index,
#                     ]
#                 else:
#                     self.sign_tracks[label][track_id][1] = self.current_frame_index

#     def _annotate_frame(self, frame, predictions, expected_label):
#         for box in predictions[0].boxes:
#             class_id = int(box.cls.item())
#             label = self.marking_classes.get(class_id)
#             if label == expected_label:
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 4)
#                 cv2.putText(
#                     frame,
#                     label,
#                     (x1, y1 - 10),
#                     cv2.FONT_HERSHEY_SIMPLEX,
#                     1.2,
#                     (0, 0, 255),
#                     3,
#                 )
#                 break
#         return frame

import os
import json
import subprocess
import traceback


BASE_DIR = os.path.dirname(__file__)
EXIFTOOL_BINARY = os.path.join(BASE_DIR, "exiftool.exe")

def extract_gps_and_timestamp(video_path, exiftool_path=EXIFTOOL_BINARY):
    """
    Extracts GPS (latitude and longitude) and timestamp from a video file using ExifTool.
    Returns (latitude, longitude, timestamp) or (None, None, None) if extraction fails.
    """
    def run_command(*args):
        try:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, _ = process.communicate()
            return stdout.decode('utf-8')
        except Exception as e:
            print(f"Command execution failed: {e}")
            print(traceback.format_exc())
            return ''

    def parse_dms(dms_str):
        dms_str = dms_str.replace("deg", "").replace("'", "").replace('"', "").strip()
        direction = dms_str[-1] if dms_str[-1] in 'NSEW' else None
        if direction:
            dms_str = dms_str[:-1].strip()
        try:
            degrees, minutes, seconds = map(float, dms_str.split())
            decimal = degrees + minutes / 60 + seconds / 3600
            if direction in ('S', 'W'):
                decimal = -decimal
            return decimal
        except ValueError:
            print(f"Invalid DMS: {dms_str}")
            return None

    # Run exiftool
    raw_json = run_command(
        exiftool_path, '-j', '-ee', '-G3', '-s',
        '-api', 'largefilesupport=1', video_path
    )
    if not raw_json:
        return None, None, None

    try:
        metadata = json.loads(raw_json)
    except json.JSONDecodeError:
        print("Failed to decode ExifTool output as JSON.")
        return None, None, None

    if not metadata:
        return None, None, None

    meta = metadata[0]
    lat = parse_dms(meta.get("Doc1:GPSLatitude", "")) if "Doc1:GPSLatitude" in meta else None
    lon = parse_dms(meta.get("Doc1:GPSLongitude", "")) if "Doc1:GPSLongitude" in meta else None

    # Get timestamp
    timestamp = meta.get("QuickTime:CreateDate") or meta.get("EXIF:DateTimeOriginal") \
        or meta.get("TrackCreateDate") or meta.get("MediaCreateDate")

    if isinstance(timestamp, str):
        timestamp = timestamp.rstrip("Z")  # Remove trailing Z
        try:
            timestamp = datetime.datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            print(f"Unrecognized timestamp format: {timestamp}")
            timestamp = None

    print(f"Latitude: {lat}, Longitude: {lon}, Timestamp: {timestamp}")
    return lat, lon, timestamp





class VideoProcessor:
    def __init__(self):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.model = YOLO(Config.COMBINED_MODEL_PATH).to(self.device)
        self.road_type_mapper = RoadTypeMapper(Config.ROAD_TYPE_MAPPER_PATH)

        self.marking_classes = {
            0: "Keep Left Divider Context",
            2: "Pedestrian Crosswalk Context",
            4: "Stop Line Context",
        }

        self.sign_classes = {
            1: "Keep Left Sign",
            3: "Pedestrian Crossing Sign",
            5: "Stop Sign",
        }

        self.expected_pairs = {
            self.marking_classes[0]: self.sign_classes[1],
            self.marking_classes[2]: self.sign_classes[3],
            self.marking_classes[4]: self.sign_classes[5],
        }

        self.marking_tracks = {}
        self.sign_tracks = {}
        self.total_frames = 1
        self.current_frame_index = 0
        self.video_path = None

    def process_video(self, video_path, tracker_path=Config.TRACKER_MODEL_PATH):
        self.video_path = video_path
        self.current_frame_index = 0

        video_capture = cv2.VideoCapture(video_path)
        self.total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            detection_results = self.model.track(
                frame,
                device=self.device,
                tracker=tracker_path,
                conf=0.5,
                persist=True,
                verbose=False,
            )

            self._update_tracking_data(detection_results)
            self.current_frame_index += 1

        video_capture.release()

    def detect_missing_signs(self, fps=60):
        missing_defects = []
        search_margin_frames = fps * 3
        video_capture = cv2.VideoCapture(self.video_path)

        for marking_label, tracked_ids in self.marking_tracks.items():
            expected_sign = self.expected_pairs.get(marking_label)
            if not expected_sign:
                continue

            intervals = list(tracked_ids.values())
            merged_intervals = self._merge_intervals(intervals)

            for start_frame, end_frame in merged_intervals:
                lower_bound = max(0, start_frame - search_margin_frames)
                upper_bound = end_frame + search_margin_frames

                found = any(
                    s_start <= upper_bound and s_end >= lower_bound
                    for s_start, s_end in self.sign_tracks.get(
                        expected_sign, {}
                    ).values()
                )

                if not found:
                    video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                    ret, frame = video_capture.read()
                    if not ret:
                        continue

                    masked_frame = self._apply_mask(frame)
                    predictions = self.model.predict(
                        masked_frame,
                        device=self.device,
                        conf=0.5,
                        verbose=False,
                    )

                    annotated_frame = self._annotate_frame(
                        frame, predictions, marking_label
                    )

                    defect_id = str(uuid.uuid4())
                    timestamp = datetime.now().strftime("%d %b %Y, %H:%M:%S")
                    image_path = os.path.join(
                        Config.DEFECT_IMGS_FOLDER, f"{defect_id}.jpg"
                    )
                    cv2.imwrite(image_path, annotated_frame)

                    defect_info = {
                        "videoId": os.path.basename(self.video_path),
                        "defectId": defect_id,
                        "defectType": f"Missing Signage ({expected_sign})",
                        "severity": None,
                        # "latitude": None,  # No GPS in this class
                        # "longitude": None,  # No GPS in this class
                        "timestamp": timestamp,
                        "imagePath": image_path,
                    }

                    missing_defects.append(defect_info)

        video_capture.release()
        return missing_defects

    def _merge_intervals(self, intervals, margin=10):
        if not intervals:
            return []
        intervals.sort()
        merged = [intervals[0]]
        for current in intervals[1:]:
            previous = merged[-1]
            if previous[1] + margin >= current[0]:
                previous[1] = max(previous[1], current[1])
            else:
                merged.append(current)
        return merged

    def _apply_mask(self, frame):
        height, width = frame.shape[:2]
        mask = np.zeros_like(frame)
        vertices = np.array(
            [
                [
                    (0, height),
                    (0, int(height / 1.5)),
                    (width, int(height / 1.5)),
                    (width, height),
                ]
            ],
            dtype=np.int32,
        )
        cv2.fillPoly(mask, vertices, (255, 255, 255))
        return cv2.bitwise_and(frame, mask)

    def _update_tracking_data(self, results):
        for box in results[0].boxes:
            if box.id is None:
                continue
            class_id = int(box.cls.item())
            track_id = f"{class_id}_{int(box.id.item())}"

            if class_id in self.marking_classes:
                label = self.marking_classes[class_id]
                if label not in self.marking_tracks:
                    self.marking_tracks[label] = {}
                if track_id not in self.marking_tracks[label]:
                    self.marking_tracks[label][track_id] = [
                        self.current_frame_index,
                        self.current_frame_index,
                    ]
                else:
                    self.marking_tracks[label][track_id][1] = self.current_frame_index

            elif class_id in self.sign_classes:
                label = self.sign_classes[class_id]
                if label not in self.sign_tracks:
                    self.sign_tracks[label] = {}
                if track_id not in self.sign_tracks[label]:
                    self.sign_tracks[label][track_id] = [
                        self.current_frame_index,
                        self.current_frame_index,
                    ]
                else:
                    self.sign_tracks[label][track_id][1] = self.current_frame_index

    def _annotate_frame(self, frame, predictions, expected_label):
        for box in predictions[0].boxes:
            class_id = int(box.cls.item())
            label = self.marking_classes.get(class_id)
            if label == expected_label:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 4)
                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0, 0, 255),
                    3,
                )
                break
        return frame
