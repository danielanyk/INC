import os
from services.video_batch import VideoBatchProcessor

MAIN_FOLDER = r"C:\Users\DanielYeoh\Downloads\9251-traffic-1\team_black_y3s1\Video_To_Process"

if __name__ == "__main__":
    processor = VideoBatchProcessor()

    for folder_name in os.listdir(MAIN_FOLDER):
        folder_path = os.path.join(MAIN_FOLDER, folder_name)
        if os.path.isdir(folder_path):
            print(f"[INFO] Start processing folder: {folder_name}")
            processor.process_folder(folder_path)
