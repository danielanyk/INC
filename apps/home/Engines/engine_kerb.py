import os
import json
import mmcv
import time
import torch
import shutil
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from ultralytics import YOLO
from mmdet.structures import DetDataSample
from mmdet.visualization import DetLocalVisualizer
from mmdet.apis import init_detector, inference_detector
from flask import Flask, request, jsonify, url_for, render_template

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)

model = None
app = Flask(__name__)
# ==== for ultralytics model ====
# default_weights_path = "./weights/best.pt"
# ==== for mmdetection model ====
default_weights_path = "apps/home/Engines/epoch/epoch_21.pth"
config_path = "apps/home/Engines/configs/kerb.py"
classes_color = [(0,0,0),(0,255,0), (0,0,255), (0,255,255)]
classes = ["Faded Kerb S1", "Faded Kerb S2", "Faded Kerb S3", "Undamaged Kerb", "Unpainted Kerb"]

@app.route("/kill_backend")
def kill_backend():
    os.kill(os.getpid(), 9)  # Send SIGKILL to the current process
    return jsonify("Server is terminating...")

@app.route("/api/load_model_kerb", methods=["POST"])
def load_model(weights_path=default_weights_path):
    global model
    start_time = time.time()
    if model is None:
        # ==== for ultralytics model ====
        # model = YOLO(weights_path)
        # ==== for mmdetection model ====
        model = init_detector(config_path, weights_path, device='cuda:0' if torch.cuda.is_available() else 'cpu')
        print(f"Model loaded in {time.time()-start_time} seconds.")
    return jsonify({"message": f"Model loaded in {(time.time() - start_time):.2f} seconds."})


@app.route("/predictKerb", methods=["POST"])
def predict():
    load_model()
    image_path = request.json.get("image_path")


    obj_list = []
    conf_list = []
    obj_name_list = []
    coords_list = []

    # ==== for ultralytics model ====
    # results = model(image_path)     
    # for result in results:
    #     for box in result.boxes:
    #         if box.cpu().numpy().cls[0] == 3 or box.cpu().numpy().cls[0] == 4 or box.cpu().numpy().conf[0] < 0.5:
    #             continue
    #         coords_list.append(box.cpu().numpy().xyxy.tolist())
    #         conf_list.append(float(box.cpu().numpy().conf[0]))
    #         obj_list.append(int(box.cpu().numpy().cls[0]))
    #         obj_name_list.append(classes[int(box.cpu().numpy().cls[0])])

    # ==== for mmdetection model ====
    img = mmcv.imread(image_path)
    img_rgb = mmcv.bgr2rgb(img)  # Convert BGR to RGB
    result = inference_detector(model, img_rgb)
    det_data_sample = DetDataSample()
    det_data_sample.pred_instances = result.pred_instances
    for sample in det_data_sample.pred_instances:
        if sample.scores.cpu().numpy() < 0.5 or sample.labels.cpu().numpy() == 3 or sample.labels.cpu().numpy() == 4:
            continue
        coords_list.append(sample.bboxes.cpu().numpy().tolist())
        conf_list.append(float(sample.scores.cpu().numpy()))
        obj_list.append(int(sample.labels.cpu().numpy()))
        obj_name_list.append(classes[int(sample.labels.cpu().numpy())])

    # ==== output ====
    output = json.dumps({"output_lbl": obj_name_list, "xyxy": coords_list, "confidence": conf_list, "class_id": obj_list})
    df = pd.read_json(output)
    df_labeled = label_neighbor_boxes(df)
    df_combined = combine_bboxes(df_labeled)    
    if len(df_combined) == 0:
        print("No kerb detected.")
        result_dict = {
            "class_id": [],
            "confidence": [],
            "output_lbl": [],
            "xyxy": []
        }
    else:
        result_dict = {
            "class_id": df_combined["class_id"].tolist(),
            "confidence": df_combined["confidence"].tolist(),
            "output_lbl": df_combined["output_lbl"].tolist(),
            "xyxy": df_combined["xyxy"].tolist()
        }
    return jsonify(result_dict)

@app.route("/clearConsole", methods=["GET"])
def clear_console():
    os.system('cls')
    return jsonify({"message": "Console cleared."})

def label_neighbor_boxes(df):
    neighbor_id = 1
    df['neighbor_id'] = 0

    for i in range(len(df)):
        x1, y1 = df.loc[i, 'xyxy'][0][0], df.loc[i, 'xyxy'][0][1]
        x2, y2 = df.loc[i, 'xyxy'][0][2], df.loc[i, 'xyxy'][0][3]
        df.loc[i,'top_left_x'] = df.loc[i, 'xyxy'][0][0]
        df.loc[i,'top_left_y'] = df.loc[i, 'xyxy'][0][1]
        df.loc[i,'bot_right_x'] = df.loc[i, 'xyxy'][0][2]
        df.loc[i,'bot_right_y'] = df.loc[i, 'xyxy'][0][3]
        current_class_id = df.loc[i, 'class_id']
        midpoint_current_x = (x1 + x2) / 2
        midpoint_current_y = (y1 + y2) / 2
        length_of_first_box = abs(x2 - x1)
        
        if df.loc[i, 'neighbor_id'] == 0:
            df.loc[i, 'neighbor_id'] = neighbor_id
            for j in range(i + 1, len(df)):
                nx1, ny1 = df.loc[j, 'xyxy'][0][0], df.loc[j, 'xyxy'][0][1]
                nx2, ny2 = df.loc[j, 'xyxy'][0][2], df.loc[j, 'xyxy'][0][3]
                next_class_id = df.loc[j, 'class_id']
                midpoint_next_x = (nx1 + nx2) / 2
                midpoint_next_y = (ny1 + ny2) / 2
                distance_between_midpoints = ((midpoint_current_x - midpoint_next_x) ** 2 + (midpoint_current_y - midpoint_next_y) ** 2) ** 0.5
                if distance_between_midpoints <= (length_of_first_box * (1.8)) and current_class_id == next_class_id:
                    df.loc[j, 'neighbor_id'] = neighbor_id
            neighbor_id += 1
    
    return df

def combine_bboxes(df):
    grouped = df.groupby('neighbor_id')

    
    combined_df = []
    for name, group in grouped:
        min_top_left_x = group['top_left_x'].min()
        min_top_left_y = group['top_left_y'].min()
        max_bottom_right_x = group['bot_right_x'].max()
        max_bottom_right_y = group['bot_right_y'].max()
        new_row = {
            'confidence': group["confidence"].mean(),  
            'output_lbl': f"{group['output_lbl'].iloc[0]} ({len(group)}m)",  # Take the class of the first item in the group
            'class_id': group['class_id'].iloc[0],  # Same logic applies here
            "xyxy": [min_top_left_x, min_top_left_y, max_bottom_right_x, max_bottom_right_y]
        }
        combined_df.append(new_row)
    return pd.DataFrame(combined_df)


if __name__ == "__main__":
    app.run(port=5003, debug = True)

