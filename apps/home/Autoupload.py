import sys
import os
import cv2
# Add project root to sys.path so 'apps' becomes importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import time
from pymongo import MongoClient
from datetime import datetime
from process import pipeline  # Adjust to your project structure
from apps.home.config import ConfigData


class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            filepath = event.src_path
            print(f"[Watchdog] New file detected: {filepath}")
            if wait_for_file_complete(filepath):
                call_pipeline(filepath)
            else:
                print("File not ready. Skipped.")

def wait_for_file_complete(path, timeout=10):
    start = time.time()
    size = -1
    while time.time() - start < timeout:
        new_size = os.path.getsize(path)
        if new_size == size:
            return True
        size = new_size
        time.sleep(0.5)
    return False

def get_video_duration(video_path):
    try:
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        
        # Check if the video is opened successfully
        if not cap.isOpened():
            print("Error: Could not open video.")
            return 0
        
        # Get the total number of frames in the video
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Get the video's frame rate (fps)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Calculate the duration in seconds by dividing the total frames by the fps
        duration = frame_count / fps
        
        cap.release()
        
        return int(duration)  # Return duration as seconds
    except Exception as e:
        print(f"Error getting video duration: {e}")
        return 0
def get_next_batch_id():
    try:
        latest = db.batch.find().sort("batchID", -1).limit(1)
        
        # Convert the cursor to a list to check if it has any items
        latest_batch = list(latest)

        if latest_batch:  # If the list is not empty, get the batchID
            return int(latest_batch[0]["batchID"]) + 1
        else:
            return 1  # If no documents found, start with batchID = 1
    except Exception as e:
        print(f"Error fetching batchID from DB: {e}")
        return 1

def call_pipeline(video_path):
    inspection_date = datetime.today().strftime("%Y-%m-%d")
    total_frames = get_video_duration(video_path)
    bid = get_next_batch_id()

    print(f"[Watchdog] Calling pipeline on: {video_path}")
    print(f"Date: {inspection_date}, Frames: {total_frames}, Batch ID: {bid}")

    pipeline(
        db=db,
        inspectionDate=inspection_date,
        path=video_path,
        tog=[True, True, True, True, True],
        lon=None,
        lat=None,
        totalframes=total_frames,
        bid=bid
    )

if __name__ == "__main__":
    client = MongoClient("mongodb://localhost:27017/FYP")
    db = client["FYP"]

    WATCH_FOLDER = r"C:\Users\DanielYeoh\Desktop\INC_video"
    print("Connecting to MongoDB at:", os.getenv("MONGO_URI"))
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_FOLDER, recursive=False)
    observer.start()
    print(f"🔍 Watching folder: {WATCH_FOLDER}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()