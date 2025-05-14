import os


class Config:
    UPLOAD_FOLDER = "uploads"
    REPORT_FOLDER = "reports"
    DEFECT_IMGS_FOLDER = "static/defect_imgs"
    TRACKER_MODEL_PATH = "models/bytetrack.yaml"
    COMBINED_MODEL_PATH = "models/combined.pt"
    ROAD_TYPE_MAPPER_PATH = "assets/road_type.csv"
    TEMPLATE_PATH = "assets/template.pdf"

    def init_app(app):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        os.makedirs(app.config["REPORT_FOLDER"], exist_ok=True)
        os.makedirs(app.config["DEFECT_IMGS_FOLDER"], exist_ok=True)
