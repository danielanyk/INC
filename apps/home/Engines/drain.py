# import argparse
# import torch
# from pathlib import Path
# from PIL import Image
# import cv2
# import numpy as np
# import pandas as pd

# from mmengine import Registry
# import mmdet.apis as da

import os
# import da
# import jsonify
# import io
from flask import Flask, request, render_template, redirect, url_for, jsonify

from ultralytics import YOLO

current_path = os.path.abspath(__file__)
APP_FOLDER = os.path.abspath(os.path.join(current_path, "../../../"))
VIDEO_FOLDER = os.path.join(APP_FOLDER, 'uploads')
UPLOAD_FOLDER = os.path.join(APP_FOLDER, 'upload_frames')
UPLOAD_DEFECTS_FOLDER = os.path.join(APP_FOLDER, 'upload_frames_defects')
REPORT_FOLDER = os.path.join(APP_FOLDER, 'reports')
# print(APP_FOLDER, 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')

# UPLOAD_FOLDER = r'C:\Y2_Sem2\INC stuff\application\upload_frames'
# UPLOAD_DEFECTS_FOLDER = r'C:\Y2_Sem2\INC stuff\application\upload_frames_defects'

app = Flask(__name__)

model = None

@app.route("/api/load_drainage", methods=["GET"])
def load_drainage(
    checkpoint= r'apps\home\Engines\epoch\B.pt',
):
    global model
    if model is None:
        model = YOLO(checkpoint)    
        print('model loaded')
    return jsonify({"message": "Model Drainage loaded successfully"})

# @app.route("/api/predict", methods=["POST"])
# def predict(
#     checkpoint= r'best.pt',
# ):
#     video_filename = request.form.get('video_filename')
#     frame_filename = request.form.get('file_name')

#     # print('video_filename',video_filename)
#     # print('frame_filename',frame_filename)
    
#     frame_path = os.path.join(UPLOAD_FOLDER, video_filename, frame_filename)
#     # print(frame_path)
#     results = model(frame_path, save = True, classes = 0)  # The model should return bounding boxes, labels, and confidence
#     for r in results:
#         if len(r.boxes) > 0:
#             if r.boxes.data[0][5] == 0:
#                 new_frame_path = os.path.join(UPLOAD_DEFECTS_FOLDER, video_filename, frame_filename)
#                 os.makedirs(os.path.dirname(new_frame_path), exist_ok=True)
#                 results[0].save(new_frame_path)
#                 data = {"is_defect_detected": True, "frame_defect_path": new_frame_path}
#                 return jsonify(data), 200
            
#     # os.rename(frame_path, new_frame_path)
#     data = {"is_defect_detected": False, "frame_defect_path": None}
#     return jsonify(data), 200

@app.route("/api/predict", methods=["POST"])
def predict():
    global model  # Make sure model is loaded before this route is hit

    data = request.get_json()
    image_path = data.get("image_path") if data else None

    if not image_path:
        return jsonify({"error": "Missing 'image_path' in request."}), 400

    try:
        # Run inference using YOLO-style model
        results = model(image_path)

        # Get detections
        boxes = results[0].boxes  # assume results is a list with 1 element
        xyxy = boxes.xyxy.tolist() if boxes.xyxy is not None else []
        class_ids = boxes.cls.tolist() if boxes.cls is not None else []
        confidences = boxes.conf.tolist() if boxes.conf is not None else []

        # Optional: you can add label names from model.names[int(cls)]
        output_lbl = ["Drainage"] if len(xyxy) > 0 else []
        print(output_lbl, xyxy, confidences, class_ids)
        return jsonify({
            "output_lbl": output_lbl,
            "xyxy": xyxy,   
            "confidence": confidences,
            "class_id": class_ids
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api", methods=["GET"])
def test(
    checkpoint= r'best.pt',
):
  return 'Bruh', 400

if __name__ == "__main__":   
    # config_file = "apps/home/Engines/configs/swin-warm-restart-final-raveling.py"
    # checkpoint = r"application\apps\engines\drain_detection_model.pt"
    checkpoint = r"apps\home\Engines\epoch\B.pt"
    model = YOLO(checkpoint)    
    app.run(debug=False, use_reloader=False, port=5009)
    

