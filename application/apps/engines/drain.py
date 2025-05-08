import argparse
import torch
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
import pandas as pd

from mmengine import Registry
import mmdet.apis as da

import os
# import da
# import jsonify
import io
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
    checkpoint= r'best.pt',
):
    global model
    if model is None:
        model = YOLO(checkpoint)    
        print('model loaded')
    return jsonify({"message": "Model ravelling loaded successfully"})

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
    global model  # Make sure the model is preloaded somewhere

    data = request.get_json()
    image_path = data.get("image_path") if data else None

    if not image_path:
        return jsonify({"error": "Missing 'image_path' in request."}), 400

    try:
        with Registry("scope").switch_scope_and_registry("mmdet"):
            result = da.inference_detector(model, image_path)

        res, output_lbl, xyxy, confidence, class_id = parse(result, image_path)

        return jsonify({
            "output_lbl": output_lbl,
            "xyxy": xyxy.tolist(),
            "confidence": confidence.tolist(),
            "class_id": class_id.tolist(),
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
    checkpoint = r"application\apps\engines\B.pt"
    model = YOLO(checkpoint)    
    app.run(debug=True, port=5009)
    

