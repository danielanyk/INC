import os
import fitz
from config import Config


class ReportGenerator:
    def __init__(self, template_path=Config.TEMPLATE_PATH):
        self.template_path = template_path

    def generate_report(self, data, address, map_stream, output_path):
        doc = fitz.open(self.template_path)

        page1 = doc[0]
        page1.insert_text((180, 100), f'{data["defectId"]}', fontsize=10)
        page1.insert_text((470, 100), f'{data["timestamp"]}', fontsize=10)
        page1.insert_text((270, 160), f'{data["roadType"]}', fontsize=10)
        page1.insert_text((470, 130), f'{data.get("severity", "Moderate")}', fontsize=10)
        page1.insert_text(
            (210, 190), f"{address['ROAD']}, {address['POSTALCODE']}", fontsize=10
        )
        page1.insert_text((210, 220), f'{data["defectType"]}', fontsize=10)

        page2 = doc[1]
        if map_stream:
            map_stream.seek(0)
            page2.insert_image(
                fitz.Rect(100, 95, 500, 400), stream=map_stream, keep_proportion=True
            )

        if data.get("imagePath") and os.path.exists(data["imagePath"]):
            page2.insert_image(
                fitz.Rect(40, 430, 290, 570),
                filename=data["imagePath"],
                keep_proportion=True,
            )

        doc.save(output_path)
