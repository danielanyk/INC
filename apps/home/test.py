from pymongo import MongoClient
import pandas as pd
import numpy as np
import supervision as sv
import cv2
import imageio
import os
from config import ConfigData
# from report import get_report_by_ID, get_bbox, generate_report
import datetime

client = MongoClient("localhost", 27017)
fdb = client["FYP"]
defect_classes = {
    "Alligator Crack": 1,
    "Arrow": 2,
    "Block Crack": 3,
    "Damaged Base Crack": 4,
    "Localised Surface Defect": 5,
    "Multi Crack": 6,
    "Parallel Lines": 7,
    "Peel Off With Cracks": 8,
    "Peeling Off Premix": 9,
    "Pothole With Crack": 10,
    "Rigid Pavement Crack": 11,
    "Single Crack": 12,
    "Transverse Crack": 13,
    "Wearing Course Peeling Off": 14,
    "White Lane": 15,
    "Yellow Lane": 16,
    "Raveling": 17,
    "Faded Kerb": 18,
    "Paint Spillage": 19,
}


def get_class_id(defect):
    print(defect, "Within get_class_id")
    # Preprocess the defect label

    preprocessed_label = defect.strip().lower()
    print(preprocessed_label)
    # Retrieve the class ID from the dictionary
    class_id = defect_classes.get(
        preprocessed_label, None
    )  # Return None if the label is not found

    if class_id is None:
        raise ValueError(f"Unknown defect label: {preprocessed_label}")
    return class_id


def apply_to_image(
    db, inspectionDate=None, bid=None, image_id=None, toggle_confidence=False
):
    image_id=2
    pipeline = [
        {
            "$lookup": {
                "from": "defect",
                "localField": "imageID",
                "foreignField": "imageID",
                "as": "defects"
            } 
        },
        {
            "$unwind": {
                "path": "$defects",
                "preserveNullAndEmptyArrays": False
            }
        },
        {
            "$match": {
                "imageID": image_id
            }
        },
        {
            "$sort": {
                "defects.defectID": 1
            }
        },
        {
            "$group": {
                "_id": "$imageID",
                "imagePath": {"$first": "$imagePath"},
                "defects": {"$push": "$defects.outputLabel"},
                "bbox": {"$push": "$defects.bbox"},
                "confidence": {"$push": "$defects.confidence"},
                "outputID": {"$push": "$defects.outputID"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "imagePath": 1,
                "imageID": "$_id",
                "defects": 1,
                "outputID": 1,
                "bbox": 1,
                "confidence": 1
            }
        }
    ]

    defected_image = list(db.image.aggregate(pipeline))
    
    # print(defected_image)

    class_id = np.array([defect_id for defect_id in defected_image[0]["outputID"]])
    bbox = np.array([eval(x) for x in defected_image[0]['bbox']])
    confidence = np.array(defected_image[0]['confidence'])
    output_lbl = list(defected_image[0]['defects'])

    if toggle_confidence == True: 
        for j in range(len(output_lbl)):
            output_lbl[j] = f"{str(output_lbl[j])} {confidence[j]:.4f}"
    output_lbl = np.array(output_lbl)

    # print(output_lbl, "Output Label", type(output_lbl))
    # print(bbox, "BBOX", type(bbox))
    # print(class_id, "Class ID", type(class_id))

    detections = sv.Detections(xyxy=bbox, confidence=confidence, class_id=class_id)
    image_path = defected_image[0]['imagePath']
    
    # box_annotator = sv.BoxAnnotator(color = sv.Color.RED, thickness=10, text_scale=3, text_color=sv.Color.WHITE, text_thickness=10)
    # annotated_frame = box_annotator.annotate(
    #     scene=cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB),
    #     detections=detections,
    #     labels=output_lbl
    # )

    # defect_img = image_path.replace(".jpg", "_defect.jpg")
    # # defect_image = image_path.replace(".png", "_defects.png")
    # imageio.imwrite(defect_img, annotated_frame)

    # for j in range(output_lbl):

    try:
        color_map = {
        'Alligator Crack': (255, 0, 0),           # Red
        'Arrow': (0, 255, 0),                     # Green
        'Blockcrack': (0, 0, 255),                # Blue
        'Damaged Base Crack': (255, 255, 0),      # Cyan
        'Localise Surface Defect': (255, 0, 255), # Magenta
        'Multicrack': (0, 255, 255),              # Yellow
        'Parallel Lines': (128, 0, 0),            # Maroon
        'Peel Off With Cracks': (128, 128, 0),    # Olive
        'Peeling Off Premix': (0, 128, 0),        # Dark Green
        'Pothole With Crack': (128, 0, 128),      # Purple
        'Rigid Pavement Crack': (0, 128, 128),    # Teal
        'Single Crack': (128, 128, 128),          # Gray
        'Transverse Crack': (0, 0, 128),          # Navy
        'Wearing Course Peeling Off': (255, 165, 0), # Orange
        'White Lane': (255, 255, 255),            # White
        'Yellow Lane': (255, 255, 0),             # Yellow
        'Raveling': (0, 0, 0),                    # Black
        'Faded Kerb': (139, 69, 19),               # Brown
        'Paint Spillage': (75, 0, 130),            # Indigo
        } 


        import matplotlib.pyplot as plt
        # Load and convert the image
        image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)

        copy_output_lbl = np.copy(output_lbl)
        for j in range(len(copy_output_lbl)):
            if "Faded Kerb" in copy_output_lbl[j]:
                copy_output_lbl[j] = "Faded Kerb" 

        # Annotate the boxes without labels
        # box_annotator = sv.BoxAnnotator(text_scale=0)  # Disable text scale for no labels
        # annotated_frame = box_annotator.annotate(scene=image, detections=detections)
    
        unique_labels = set(copy_output_lbl)
        legend = {label: color_map[label] for label in unique_labels}
        
        for i in range(len(detections)):
            x1, y1, x2, y2 = map(int, bbox[i]) 
            color = legend[copy_output_lbl[i]]
            cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness = 15)  

        image_height, image_width = image.shape[:2]
        legend_height = 50 + len(legend) * 60
        legend_canvas = np.ones((legend_height, image_width, 3), dtype=np.uint8) * 255  

        font_scale = 3
        thickness = 6

        for idx, (label, color) in enumerate(legend.items()):
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            text_width, text_height = text_size[0]

            rect_width = 30  
            rect_height = text_height + 10  
            
            top_left = (20, 20 + idx * (rect_height + 20))  
            bottom_right = (20 + rect_width, 20 + idx * (rect_height + 20) + rect_height)
            cv2.rectangle(legend_canvas, top_left, bottom_right, color, -1)
            
            text_x = bottom_right[0] + 10
            text_y = top_left[1] + rect_height - 5
            
            cv2.putText(legend_canvas, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)

        combined_image = np.vstack((image, legend_canvas))
        plt.imshow(combined_image)
        plt.axis('off')  
        plt.show()
        legend_save_path = image_path.replace(".jpg", "_legend_defect.jpg")
        plt.savefig(legend_save_path, bbox_inches='tight', pad_inches=0, format='jpg')
    except:
        print('hi')



apply_to_image(db=fdb, image_id=4, inspectionDate="27/7/2024", toggle_confidence=False)
