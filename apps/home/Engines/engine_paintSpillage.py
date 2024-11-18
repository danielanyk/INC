import os
import ultralytics
from ultralytics import YOLO
import glob

ultralytics.checks()
# from roboflow import Roboflow
import cv2
import numpy as np
import shutil
from flask import Flask, request, jsonify
import torch
import cv2
import supervision as sv

app = Flask(__name__)

# Initialize your model globally
model = None
confidence = 0.35


# load model
@app.route("/api/load_model_paintSpillage", methods=["POST"])
def load_model(weights_file="./epoch/best (4).pt"):
    global model
    weights_file = os.path.join(os.path.dirname(__file__), "./epoch/best (4).pt")
    if model is None:
        model = YOLO(model=weights_file)    
    return jsonify({"message": "Model loaded successfully"})

@app.route('/shutdown', methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        os.kill(os.getpid(), 9)  # Send SIGKILL to the current process
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

@app.route("/predictPaint", methods=["POST"])
def predict():
    if model is None:
        load_model()
    # =============== PRED AND REMOVE MASK =================
    filepath = request.json.get("image_path")

    # Iterate through each image file
    results = model.predict(source=filepath, conf=confidence, save=False)
    if results:
        for result in results:
            if result.masks is not None:
                masks_np = result.masks.data

                for mask in masks_np:
                    mask_cpu = mask.cpu()
                    mask_np = mask_cpu.numpy()
                    print(mask_np, "mask_np")

                    for box in result.boxes.xyxy:
                        x_min, y_min, x_max, y_max = box.cpu().numpy().astype(int)
                        cv2.rectangle(
                            result.orig_img,
                            (x_min, y_min),
                            (x_max, y_max),
                            (0, 255, 0),
                            2,
                        )
                        class_name = result.names[0]
                        confidence_score = result.boxes.conf[0].cpu().item()
                        label_text = (
                            f"{class_name.capitalize()}" + " " + str("Spillage")
                        )
                        cv2.putText(
                            result.orig_img,
                            label_text,
                            (int(x_min), int(y_min) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.9,
                            (0, 255, 0),
                            2,
                        )
                    print("label_text", label_text)
                    print("confidence_score", confidence_score)
                    print("result.boxes", result.boxes.xyxy.cpu().numpy().tolist())
                    return jsonify(
                        {
                            "output_lbl": [label_text],
                            "xyxy": result.boxes.xyxy.cpu().numpy().tolist(),
                            "confidence": [confidence_score],
                            "class_id": [19],
                        }
                    )
            else:
                return jsonify(
                    {"output_lbl": [], "xyxy": [], "confidence": [], "class_id": []}
                )
    else:
        return jsonify(
            {"output_lbl": "", "xyxy": [], "confidence": 0, "class_id": None}
        )


if __name__ == "__main__":
    app.run(debug=True, port=5004)
