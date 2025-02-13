import cv2
import os
import subprocess
from flask import Flask, jsonify, send_from_directory, Blueprint
import requests
from PIL import Image
import io
from routes import report
import app


current_path = os.path.abspath(__file__)
APP_FOLDER = os.path.abspath(os.path.join(current_path, "../../../"))
VIDEO_FOLDER = os.path.join(APP_FOLDER, 'uploads')
UPLOAD_FOLDER = os.path.join(APP_FOLDER, 'upload_frames')
UPLOAD_DEFECTS_FOLDER = os.path.join(APP_FOLDER, 'upload_frames_defects')
REPORT_FOLDER = os.path.join(APP_FOLDER, 'reports')


def start_upload_file(filename):
    print(extract_frames(filename))
    print("DONE")
    # return render_template('index.html')
    return 'Done', 200

def extract_frames(video_filename):
    video_path = os.path.join(VIDEO_FOLDER, video_filename)
    if not os.path.exists(video_path):
        return jsonify({'error': 'Video file not found'}), 404
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return jsonify({'error': 'Failed to open video'}), 500
    
    frames = []
    fps = cap.get(cv2.CAP_PROP_FPS)  # Get frames per second
    frame_rate = int(fps)  # We want to get a frame every second
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    total_seconds = total_frames / fps
    total_seconds = total_seconds - total_seconds % 1 + 3

    
    # Loop over the video and capture the first frame per second
    count = 0
    defect_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Current position in the video (in frames)
        current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
        
        # If the current frame corresponds to the start of a new second
        if current_frame % frame_rate == 1:  # 1-based index for seconds
            count += 1
            
            # if count == 2:
            #     break
            
            frame_filename = f"frame_{int(current_frame)}.jpg"
            frame_folder_path = os.path.join(UPLOAD_FOLDER, video_filename)
            frame_path = os.path.join(UPLOAD_FOLDER, video_filename, frame_filename)
            os.makedirs(os.path.dirname(frame_path), exist_ok=True)
            cv2.imwrite(frame_path, frame)  # Save frame as an image
            
            print(video_filename)
            print(frame_filename)
            data = {'video_filename': video_filename, 'file_name' : frame_filename}
            response = requests.post('http://localhost:5009/api/predict', data=data)
            response_data = response.json()
            if response_data['is_defect_detected'] == True:
                defect_count += 1
                report.create_report(response_data['frame_defect_path'], video_filename, count)
            
            
                    
    cap.release()
    
    # Return the list of frame file names as a response
    return jsonify({'frame': response.text})
