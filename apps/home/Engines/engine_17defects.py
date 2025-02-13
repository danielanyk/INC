from flask import Flask, request, jsonify

# import Flask
# import requests
# import jsonify
import mmdet.apis as da
import torch
from mmengine import Registry
import cv2
import supervision as sv
import numpy as np
from ensemble_boxes import *
# from your_model import YourModel  # Import your model class
import os
app = Flask(__name__)

# Initialize your model globally
classes = (
    "Alligator Crack",
    "Arrow",
    "Block Crack",
    "Damaged Base Crack",
    "Localise Surface Defect",
    "Multi Crack",
    "Parallel Lines",
    "Peel Off With Cracks",
    "Peeling Off Premix",
    "Pothole With Crack",
    "Rigid Pavement Crack",
    "Single Crack",
    "Transverse Crack",
    "Wearing Course Peeling Off",
    "White Lane",
    "Yellow Lane",
)

deviceglob = torch.device("cuda" if torch.cuda.is_available() else "cpu")

@app.route('/shutdown', methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        os.kill(os.getpid(), 9)  # Send SIGKILL to the current process
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

@app.route("/api/load_model_17defects", methods=["POST"])
def load_model(
    cfgdet="apps/home/Engines/configs/swin-warm-restart-final.py",
    ckpdet1="apps/home/Engines/epoch/epoch_79.pth",
    ckpdet2="apps/home/Engines/epoch/epoch_80.pth",
):
    global models
    # MMDET Models
    models = [
        da.init_detector(
            cfgdet,
            checkpoint=ckpdet1,
            device=deviceglob,
        ),
        da.init_detector(
            cfgdet,
            checkpoint=ckpdet2,
            device=deviceglob,
        ),
    ]
    return jsonify({"message": "Model loaded successfully"})

@app.route("/predict17Defects", methods=["POST"])
def predict():
    image_path = request.json.get("image_path")

    if image_path == "" or image_path is None:
        image_path = "Testing_and_YAML_files/test_image.png"

    ls = []
    conf_ls = []
    class_ls = []
    global models
    for model in models:
        with Registry("scope").switch_scope_and_registry("mmdet"):
            result = da.inference_detector(model, image_path)

        xy, conf, class_id, w, h, im = parse(result, image_path)
        ls.append(xy)
        conf_ls.append(conf)
        class_ls.append(class_id)

    detections, output_lbl = weightedboxfusion(ls, conf_ls, class_ls, [4, 1], w, h)

    xyxy = detections.xyxy.tolist()
    labels = detections.class_id.tolist()
    confidence = detections.confidence.tolist()

    print("17DEFECTS", xyxy, labels, confidence, output_lbl)

    return jsonify({"xyxy": xyxy, "class_id": labels, "confidence": confidence, "output_lbl": output_lbl})

def parse(res, image_path):
    im = cv2.imread(image_path)
    h, w, _ = im.shape

    print(h,w, _ , "H, W, _")

    box_annotator = sv.BoxAnnotator(text_scale=1.0)
    det = sv.Detections(
        xyxy=res.pred_instances["bboxes"].cpu().numpy(),
        confidence=res.pred_instances["scores"].cpu().numpy(),
        class_id=res.pred_instances["labels"].cpu().numpy().astype(int),
    )
    
    det = det[det.confidence > 0.4]
    detections = det[det.area > 150]


    for dets in detections.xyxy:
        dets[0] = dets[0] / w
        dets[1] = dets[1] / h
        dets[2] = dets[2] / w
        dets[3] = dets[3] / h

    return detections.xyxy.tolist(), detections.confidence.tolist(), detections.class_id.tolist(), w, h, im

def weightedboxfusion(ls, conf_ls, class_ls, weights, w, h):
    # print("Configs for weighted boxes fusion (1st set of Models)")
    # print(ls, conf_ls, class_ls, weights)

    boxes, scores, labels = weighted_boxes_fusion(
        ls,
        conf_ls,
        class_ls,
        weights=weights,
        iou_thr=0.3,
        skip_box_thr=0.05,
    )

    for dets in boxes:
        dets[0] = dets[0] * w
        dets[1] = dets[1] * h
        dets[2] = dets[2] * w
        dets[3] = dets[3] * h

    detections = sv.Detections(
        xyxy=boxes,
        confidence=scores,
        class_id=np.array(labels, dtype=int),
    )

    print("After Weighted Box Fusion", detections.xyxy.tolist(), detections.confidence.tolist(), detections.class_id.tolist())
    detections = detections[detections.confidence > 0.5]
    try:
        output_lbl = [f"{classes[int(class_id)]}" for _, _, confidence, class_id, _ in detections]
    except:
        output_lbl = [f"{classes[int(class_id)]}" for _, _, confidence, class_id, _, _ in detections]

    return detections, output_lbl

if __name__ == "__main__":
    print("hi")
    app.run(debug=True, port=5002)
    load_model()
