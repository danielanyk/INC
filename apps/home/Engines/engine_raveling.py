from flask import Flask, request, jsonify
import mmdet.apis as da
import torch
from mmengine import Registry
import cv2
import supervision as sv
import numpy as np
import pickle
import base64
import os
# from your_model import YourModel  # Import your model class

app = Flask(__name__)
classes = ("raveling",)

model = None


@app.route("/api/load_model_raveling", methods=["POST"])
def load_model(
    config_file="apps/home/Engines/configs/swin-warm-restart-final-raveling.py",
    checkpoint="apps/home/Engines/epoch/epoch_24.pth",
):
    global model
    if model is None:
        model = da.init_detector(
            config_file,
            checkpoint=checkpoint,
            device="cuda:0" if torch.cuda.is_available() else "cpu",
        )  # Load your model here
        print('model loaded')
    return jsonify({"message": "Model loaded successfully"})

@app.route("/predictRaveling", methods=["POST"])
def predict():
    global model
    image_path = request.json.get("image_path")
    if image_path == "" or image_path is None:
        image_path = "Testing_and_YAML_files/test_image.png"

    with Registry("scope").switch_scope_and_registry("mmdet"):
        result = da.inference_detector(model, image_path)

    res, output_lbl, xyxy, confidence, class_id = parse(result, image_path)

    xyxy = xyxy.tolist()
    confidence = confidence.tolist()
    class_id = class_id.tolist()
    
    return jsonify(
        {
            "output_lbl": output_lbl,
            "xyxy": xyxy,
            "confidence": confidence,
            "class_id": class_id,
        }
    )


def parse(res, image_path):
    with Registry("scope").switch_scope_and_registry("mmdet"):
        results = da.inference_detector(model, image_path)
    im = cv2.imread(image_path)
    h, w, _ = im.shape

    box_annotator = sv.BoxAnnotator(text_scale=1.0)
    det = sv.Detections(
        xyxy=results.pred_instances["bboxes"].cpu().numpy(),
        confidence=results.pred_instances["scores"].cpu().numpy(),
        class_id=results.pred_instances["labels"].cpu().numpy().astype(int),
    )

    det = det[det.confidence > 0.5]
    detections = det[det.area > 300]
    try:
        output_lbl = [f"Raveling" for _, _, confidence, class_id,_ in detections]
    except:
        output_lbl = [f"Raveling" for _, _, confidence, class_id,_, _ in detections]

    return res, output_lbl, detections.xyxy, detections.confidence, detections.class_id


@app.route('/shutdown', methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        os.kill(os.getpid(), 9)
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

if __name__ == "__main__":   
    config_file = "apps/home/Engines/configs/swin-warm-restart-final-raveling.py"
    checkpoint = "apps/home/Engines/epoch/epoch_24.pth"
    model = da.init_detector(
        config_file,
        checkpoint=checkpoint,
        device="cuda:0" if torch.cuda.is_available() else "cpu",
    )
    app.run(debug=False, use_reloader=False, port=5001)
    
