import os
import time
import torch
import mmcv
import cv2
import numpy as np
from ultralytics import YOLO
from mmdet.apis import init_detector, inference_detector
from mmengine.registry import Registry
from ensemble_boxes import weighted_boxes_fusion
import supervision as sv

class EngineManager:
    """
    Manages multiple detection engines (YOLO or MMDetection ensembles) for inference.
    Ensures class IDs map to database DefectTypeID values, and outputs fields in the order:
    output_lbl, xyxy, confidence, class_id
    """
    ENGINES = {
        "kerb": {
            "type": "mmdet",
            "config": "models/kerb.py",
            "weights": "models/epoch_21.pth",
            "classes": ["Damaged Kerb","Damaged Kerb","Damaged Kerb","Undamaged Kerb","Damaged Kerb"],
            "class_ids": [21, 21, 21, 21, 21],
        },
        "paintSpillage": {
            "type": "yolo",
            "weights": "models/best (4).pt",
            "classes": ["Paint Spillage"],
            "class_ids": [22],
        },
        "raveling": {
            "type": "mmdet",
            "config": "models/swin-warm-restart-final-raveling.py",
            "weights": "models/epoch_24.pth",
            "classes": ["No Raveling","Raveling"],
            "class_ids": [20,20],
        },
        "defects17": {
            "type": "ensemble_mmdet",
            "config": "models/swin-warm-restart-final.py",
            "weights": [
                "models/epoch_79.pth",
                "models/epoch_80.pth"
            ],
            "classes": [
                "Alligator Crack","Arrow","Block Crack","Damaged Base Crack","Localise Surface Defect",
                "Multi Crack","Parallel Lines","Peel Off With Cracks","Peeling Off Premix","Pothole With Crack",
                "Rigid Pavement Crack","Single Crack","Transverse Crack","Wearing Course Peeling Off",
                "White Lane","Yellow Lane"
            ],
            "class_ids": [4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19],
            "fusion_weights": [4, 1]
        },
        "drainage": {
            "type": "yolo",
            "weights": "models/B.pt",  # Adjust to actual path
            "classes": ["Drainage","Drainage"],
            "class_ids": [23,23],  # Use a unique DefectTypeID
        },
        "trenches": {
            "type": "yolo",
            "weights": "models/best.pt",  
            "classes": ["Trenches","Trenches"],
            "class_ids": [24,24],
        },
    }

    def __init__(self):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self._models = {}

    def load_engine(self, name):
        if name not in self.ENGINES:
            raise ValueError(f"Unknown engine '{name}'")
        if name in self._models:
            return f"Engine '{name}' already loaded"
        cfg = self.ENGINES[name]
        start = time.time()
        if cfg["type"] == "yolo":
            model = YOLO(cfg["weights"])
        elif cfg["type"] in ("mmdet", "ensemble_mmdet"):
            weights = cfg["weights"]
            if isinstance(weights, list):
                model = [init_detector(cfg["config"], w, device=self.device) for w in weights]
            else:
                model = init_detector(cfg["config"], weights, device=self.device)
        else:
            raise ValueError(f"Unsupported engine type '{cfg['type']}'")
        self._models[name] = model
        return f"Loaded '{name}' in {time.time() - start:.2f}s"

    def predict(self, name, image_path, conf_threshold=0.5):
        if name not in self.ENGINES:
            raise ValueError(f"Unknown engine '{name}'")
        if name not in self._models:
            self.load_engine(name)
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        cfg = self.ENGINES[name]
        model = self._models[name]
        if cfg["type"] == "yolo":
            return self._predict_yolo(name, model, image_path, conf_threshold)
        return self._predict_mmdet(name, model, image_path, conf_threshold)

    def _predict_yolo(self, name, model, image_path, conf_threshold):
        cfg = self.ENGINES[name]
        results = model.predict(source=image_path, conf=conf_threshold, save=False, verbose=False)
        if not results or not results[0].boxes:
            return {"output_lbl": [], "xyxy": [], "confidence": [], "class_id": []}
        r = results[0]
        coords = r.boxes.xyxy.cpu().numpy().tolist()
        confs  = r.boxes.conf.cpu().numpy().tolist()
        idxs   = [int(c) for c in r.boxes.cls.cpu().numpy().tolist()]
        class_ids = [cfg['class_ids'][i] for i in idxs]
        labels = [cfg['classes'][i] for i in idxs]
        return {"output_lbl": labels, "xyxy": coords, "confidence": confs, "class_id": class_ids}

    def _predict_mmdet(self, name, model, image_path, conf_threshold):
        cfg = self.ENGINES[name]
        img = mmcv.imread(image_path)
        img = mmcv.bgr2rgb(img)

        def run_amp_inference(m):
            with Registry("scope").switch_scope_and_registry("mmdet"):
                if self.device.type == "cuda":
                    with torch.cuda.amp.autocast():
                        return inference_detector(m, img)
                else:
                    return inference_detector(m, img)

        if isinstance(model, list):
            all_boxes, all_scores, all_idxs = [], [], []
            for m in model:
                res = run_amp_inference(m)
                b, s, idxs = self._parse_detections(res, img, conf_threshold)
                all_boxes.append(b)
                all_scores.append(s)
                all_idxs.append(idxs)
            detections, class_ids = self._fuse_boxes(
                all_boxes, all_scores, all_idxs,
                cfg.get("fusion_weights"), img.shape[1], img.shape[0], cfg
            )
            id_to_label = dict(zip(cfg['class_ids'], cfg['classes']))
            labels = [id_to_label.get(int(cid), f"Unknown({cid})") for cid in class_ids]
            # print(detections.xyxy.tolist(), detections.confidence.tolist(), class_ids)
            return {
                "output_lbl": labels,
                "xyxy": detections.xyxy.tolist(),
                "confidence": detections.confidence.tolist(),
                "class_id": class_ids
            }
        else:
            res = run_amp_inference(model)
            boxes, scores, idxs = self._parse_detections(res, img, conf_threshold)
            # print(boxes, scores, idxs)
            class_ids = [cfg['class_ids'][i] for i in idxs]
            labels = [cfg['classes'][i] for i in idxs]
            return {
                "output_lbl": labels,
                "xyxy": boxes,
                "confidence": scores,
                "class_id": class_ids
            }

    def _parse_detections(self, res, img, conf_threshold):
        h, w, _ = img.shape
        det = sv.Detections(
            xyxy=res.pred_instances["bboxes"].cpu().numpy(),
            confidence=res.pred_instances["scores"].cpu().numpy(),
            class_id=res.pred_instances["labels"].cpu().numpy().astype(int),
        )
        det = det[det.confidence > conf_threshold]
        det = det[det.area > 150]
        for box in det.xyxy:
            box[0] /= w; box[1] /= h; box[2] /= w; box[3] /= h
        return det.xyxy.tolist(), det.confidence.tolist(), det.class_id.tolist()

    def _fuse_boxes(self, boxes_list, scores_list, labels_list, weights, w, h, cfg):
        fb, fs, fl = weighted_boxes_fusion(
            boxes_list, scores_list, labels_list,
            weights=weights, iou_thr=0.3, skip_box_thr=0.05
        )
        for box in fb:
            box[0] *= w; box[1] *= h; box[2] *= w; box[3] *= h
        det = sv.Detections(xyxy=fb, confidence=fs, class_id=np.array(fl, dtype=int))
        det = det[det.confidence > 0.5]
        return det, fl
