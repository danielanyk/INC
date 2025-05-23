from flask import Flask, request, jsonify
import os
from os import listdir
from os.path import isfile, join
import datetime
import subprocess
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import tempfile
import webbrowser
from PIL import Image, ImageDraw
from apps.home.onemap_service import generate_static_map
from apps.home.config import ConfigData

# db=mongo.db
client = MongoClient("mongodb://localhost:27017/FYP")
# db = client["FYP"]
db=client['newdb']

# def lookup_reports(ids):
#     """
#     Returns reports by reportID; used for AI summarizer
#     """
#     pipeline = [
#         {"$match": {"reportID": {"$in": ids}}},
#         {
#             "$lookup": {
#                 "from": "image",
#                 "localField": "imageid",
#                 "foreignField": "imageid",
#                 "as": "imageData",
#             }
#         },
#         {"$unwind": "$imageData"},
#         {
#             "$lookup": {
#                 "from": "defect",
#                 "localField": "imageData.imageid",
#                 "foreignField": "imageid",
#                 "as": "defectData",
#             }
#         },
#         {"$unwind": "$defectData"},
#         {
#             "$group": {
#                 "_id": "$imageData.imageid",
#                 "reportID": {"$first": "$reportID"},
#                 "inspectedBy": {"$first": "$inspectedBy"},
#                 "inspectionDate": {"$first": "$inspectionDate"},
#                 "generationTime": {"$first": "$generationTime"},
#                 "tags": {"$first": "$tags"},
#                 "defects": {
#                     "$push": {
#                         "outputLabel": "$defectData.outputLabel",
#                         "confidence": "$defectData.confidence",
#                     }
#                 },
#             }
#         },
#         {
#             "$project": {
#                 "reportID": 1,
#                 "inspectedBy": 1,
#                 "inspectionDate": 1,
#                 "generationTime": 1,
#                 "tags": 1,
#                 "defects": 1,
#                 "_id": 0,
#             }
#         },
#     ]
#     reports = db["report"].aggregate(pipeline)

#     return {"reports": list(reports)}


def get_filter_tags():
    """
    Returns the location tags from the database
    """
    batches = db["batch"].distinct("batchPath")
    defects = db["defect"].distinct("outputLabel")
    town_tags = db["image"].distinct("town")
    custom_tags = db["report"].distinct("tags")
    split_tags = []
    for tag in custom_tags:
        split_tags.extend(tag.split(", "))

    split_batches = []
    for batchname in batches:
        batchname = batchname.split("\\")[-1]
        batchname = batchname.split(".")[0]
        split_batches.append(batchname)

    consolidated = []
    for defect in defects:
        if "Faded Kerb" in defect:
            if "Faded Kerb" not in consolidated:
                consolidated.append("Faded Kerb")
        else:
            consolidated.append(defect)

    return (
        split_batches[::-1],
        list(set(consolidated)),
        list(town_tags),
        list(set(split_tags)),
    )


def get_amount_of_defects():
    """
    Returns the amount of defects in the database
    """
    result = db.defect.aggregate(
        [
            {
                "$addFields": {
                    # Standardize the label for Faded Kerb
                    "standardizedLabel": {
                        "$switch": {
                            "branches": [
                                {
                                    "case": {
                                        "$regexMatch": {
                                            "input": "$outputLabel",
                                            "regex": "^Faded Kerb",
                                        }
                                    },
                                    "then": "Faded Kerb",
                                },
                            ],
                            "default": "$outputLabel",
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "severity": "$severity",
                        "outputLabel": "$standardizedLabel",
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id.severity": 1, "count": -1}},
            {
                "$project": {
                    "_id": 0,
                    "Severity": "$_id.severity",
                    "Defect": "$_id.outputLabel",
                    "Count": "$count",
                }
            },
        ]
    )

    return list(result)


def get_bbox(imageid):
    """
    Returns a list of bounding box coordinates for a specific imageid
    """
    results = db.defect.find({"imageid": imageid})

    bounding_boxes = []
    for result in results:
        bounding_boxes.append(result["bbox"])
    return bounding_boxes if bounding_boxes else None


def repeated_defects(types, road):
    """
    Checks if there are repeated defects (same defect type on the same road) in the database.
    Returns 'Yes' if repeated defects are found, 'No' otherwise.
    """
    pipeline = [
        {
            "$lookup": {
                "from": "defect",
                "localField": "imageid",
                "foreignField": "imageid",
                "as": "DefectData",
            }
        },
        {
            "$lookup": {
                "from": "image",
                "localField": "imageid",
                "foreignField": "imageid",
                "as": "ImageData",
            }
        },
        {"$unwind": "$ImageData"},
        {"$unwind": {"path": "$DefectData", "preserveNullAndEmptyArrays": True}},
        {"$match": {"ImageData.road": road, "DefectData.outputLabel": types}},
        {
            "$group": {
                "_id": {
                    "road": "$ImageData.road",
                    "defectType": "$DefectData.outputLabel",
                },
                "count": {"$sum": 1},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
        {"$count": "totalCount"},
    ]

    result = list(db.report.aggregate(pipeline))

    if result:
        if result[0]["totalCount"] > 2:
            print(result)
            return "Yes"
        else:
            return "No"
    else:
        return "No"

#KYUI CHECK HERE FOR REPORT IMAGE, Here
def get_reports(tags=None, start=0, end=30, image_id=None):
    """
    Returns the 30 latest reports from the database, latest batch shown first in report page.
    """

    print(image_id)
    print(tags)
    print(start, end)

    if tags is None:
        tags = {
            "Batch": None,
            "Defect Type": None,
            "Severity": None,
            "Location": None,
            "Custom Tag": None,
            "DateStart": None,
            "DateEnd": None,
        }

    pipeline = []

    pipeline.extend(
        [
            {
                "$lookup": {
                    "from": "defect",
                    "localField": "imageid",
                    "foreignField": "imageid",
                    "as": "DefectData",
                }
            },
            {
                "$lookup": {
                    "from": "report",
                    "localField": "imageid",
                    "foreignField": "imageid",
                    "as": "ReportData",
                }
            },
            {
                "$unwind": "$DefectData",
                "$unwind": "$ReportData",
            },
            {
                "$project": {
                    # info for the report
                    "_id": 0,
                    "Name": {
                        "$arrayElemAt": [
                            {
                                "$split": [
                                    {
                                        "$arrayElemAt": [
                                            {"$split": ["$imagePath", "\\"]},
                                            -1,
                                        ]
                                    },
                                    ".",
                                ]
                            },
                            0,
                        ]
                    },
                    "Severity": "$DefectData.severity",
                    "Inspection Type": "$ReportData.inspectionType",
                    "Inspection Date": "$ReportData.inspectionDate",
                    "RoadType": "$roadType",
                    "Type": "$DefectData.outputLabel",
                    "Latitude": "$latitude",
                    "Longitude": "$longitude",
                    "Inspector": "$ReportData.inspectedBy",
                    "Generation Date": "$ReportData.generationTime",
                    "Image": {
                        "$concat": [
                            {"$arrayElemAt": [{"$split": ["$imagePath", "."]}, 0]},
                            "_defect.",
                            {"$arrayElemAt": [{"$split": ["$imagePath", "."]}, 1]},
                        ]
                    },
                    "Town": "$town",
                    "Custom Tag": "$ReportData.tags",
                    "ReportID": "$ReportData.reportID",
                    "Road": "$road",
                    "imageid": "$imageid",
                    "Quantity": "$ReportData.quantity",
                    "Measurement": "$ReportData.measurement",
                    "Cause": "$ReportData.cause",
                    "Recommendation": "$ReportData.recommendation",
                    "Remarks": "$ReportData.remarks",
                    "Supervisor": "$ReportData.supervisor",
                    "Via": "$ReportData.via",
                    "Acknowledgement": "$ReportData.acknowledgement",
                    "Confidence": "$DefectData.confidence",
                }
            },
        ]
    )
    if image_id:
        pipeline.append(
            {
                "$match": {
                    "imageid": image_id,
                }
            }
        )
    if tags:
        if tags["DateStart"] is not None and tags["DateEnd"] is not None:
            if tags["DateStart"] == tags["DateEnd"]:
                pipeline.append(
                    {
                        "$match": {
                            "Inspection Date": tags["DateStart"],
                        }
                    }
                )
            else:
                pipeline.append(
                    {
                        "$match": {
                            "Inspection Date": {
                                "$gte": tags["DateStart"],
                                "$lte": tags["DateEnd"],
                            }
                        }
                    }
                )
        if tags["Defect Type"] != None and tags["Defect Type"] != []:
            pipeline.append(
                {
                    "$match": {
                        "Type": {"$regex": "|".join(tags["Defect Type"])},
                    }
                }
            )
        if tags["Severity"] != None:
            pipeline.append(
                {
                    "$match": {
                        "Severity": tags["Severity"],
                    }
                }
            )

        if tags["Location"] != None:
            pipeline.append(
                {
                    "$match": {
                        "Town": tags["Location"],
                    }
                }
            )
        if tags["Custom Tag"] != None:
            pipeline.append(
                {"$match": {"Custom Tag": {"$regex": f"\\b{tags['Custom Tag']}\\b"}}}
            )

        if tags["Batch"] != None:
            pipeline.append({"$match": {"Image": {"$regex": f"\\b{tags['Batch']}\\b"}}})

    pipeline.append({"$sort": {"Name": 1}})
    reports = db["image"].aggregate(pipeline)
    reports = list(reports)

    return reports[start:end]


def template3(c, view_report):
    companylogo = ConfigData.COMPANY_NAME + ".png"
    print(os.getcwd())
    logo_path = os.path.join(
        os.getcwd(), "apps", "static", "dist", "img", companylogo
    )
    
    y_position = 650
    
    try:
        c.drawImage(logo_path, 200, y_position+30, width=200, height=100)
        y_position -= 120 
    except FileNotFoundError:
        # Adjust the Y position since logo is not available
        y_position -= 50  
    except Exception as e:
        print("An error occurred:", e)
        # Adjust the Y position since logo is not available
        y_position -= 50  

    # Adjust the rest of the content based on the Y position
    if view_report["severity"] == 3:
        c.setFillColorRGB(1, 0, 0)
        txt = "This is a high severity defect. Please take immediate action."
        view_report["severity"] = "High"
    elif view_report["severity"] == 2:
        c.setFillColorRGB(1, 0.8, 0)
        txt = "This is a medium severity defect. Please take action soon."
        view_report["severity"] = "Medium"
    else:
        c.setFillColorRGB(0, 1, 0)
        txt = "This is a low severity defect. Please take action when possible."
        view_report["severity"] = "Low"

    unique_types = set()
    for issue in view_report["type"]:
        if issue.startswith("Faded Kerb"):
            unique_types.add("Faded Kerb")
        else:
            unique_types.add(issue)

    view_report["type"] = ", ".join(unique_types)

    c.rect(60, y_position + 80, 500, 50, fill=True)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(110, y_position + 100, txt)
    
    # Draw the header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(210, y_position + 60, "Defect Record Sheet")

    c.rect(60, y_position - 230, 500, 280, fill=False)
    c.setFont("Helvetica", 12)

    headers = [
        "Name:",
        "Inspection Type:",
        "Inspection Date:",
        "Road Type:",
        "Defect Type:",
        "Latitude:",
        "Longitude:",
        "Inspector:",
        "Severity:",
    ]

    max_header_width = max(
        c.stringWidth(header, "Helvetica-Bold", 12) for header in headers
    )

    # Draw the headers
    y_start = y_position
    for header in headers:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(70, y_start, header)
        y_start -= 25

    view_report_content = [
        view_report["name"].split(".")[0],
        view_report["ins_type"],
        view_report["ins_date"],
        view_report["road_type"],
        view_report["type"],
        view_report["latitude"],
        view_report["longitude"],
        view_report["inspector"],
        view_report["severity"],
    ]

    def draw_wrapped_text(c, text, x, y, max_width, font_name, font_size):
        if not isinstance(text, str):
            text = str(text)  # Convert to string if it's not already
        words = text.split(' ')
        print(words)
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            text_width = c.stringWidth(test_line, font_name, font_size)
            if text_width > max_width:
                c.drawString(x, y + 10, line.strip())
                y -= font_size - 10
                line = word
            else:
                line = test_line
        if line:
            c.drawString(x, y, line.strip())

    underline_y = y_position
    y_start = y_position
    max_width = 330

    for text in view_report_content:
        c.setFont("Helvetica", 12)
        if text == view_report["type"]:
            print(text)
            draw_wrapped_text(c, text, 200, y_start, max_width, "Helvetica", 12)
            y_start -= 25
        else:
            if not isinstance(text, str):
                text = str(text)  
            c.drawString(35 + max_header_width + 70, y_start, text)
            c.line(200, underline_y - 3, 530, underline_y - 3)
            y_start -= 25
            underline_y -= 25
            c.line(200, underline_y - 3, 530, underline_y - 3)
    
    image_path = view_report["image"].replace("_defect", "_legend_defect")
    c.setLineWidth(2)
    c.rect(60, y_start - 300, 500, 280)
    try:
        c.drawImage(image_path, 61, y_start - 299, width=498, height=278)
    except FileNotFoundError:
        print("Image file not found.")
        c.drawString(250, 150, "Image not available")
    except Exception as e:
        print("An error occurred:", e)
        c.drawString(250, 150, "Image not available")

    return c


def template2(c, view_report):
    unique_types = set()
    for issue in view_report["type"]:
        if issue.startswith("Faded Kerb"):
            unique_types.add("Faded Kerb")
        else:
            unique_types.add(issue)

    view_report["type"] = ", ".join(unique_types)

    width, height = letter

    c.setFillColorRGB(0.941, 0.941, 0.941)
    c.setStrokeColor(colors.white)
    c.rect(30, height - 765, 550, 728, fill=True)

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2.0, height - 60, "DEFECT RECORD SHEET")

    c.setStrokeColor(colors.blue)
    c.line(50, height - 70, 550, height - 70)

    if view_report["severity"] == 3:
        c.setFillColorRGB(255 / 255, 38 / 255, 36 / 255)
        colorscheme = {
            1: (254 / 255, 128 / 255, 140 / 255),
            2: (254 / 255, 178 / 255, 186 / 255),
        }
        txt = "This is a high severity defect. Please take immediate action."
        view_report["severity"] = "High"
    elif view_report["severity"] == 2:
        c.setFillColorRGB(0.8, 0.388, 0.18)
        colorscheme = {
            1: (0.839, 0.78, 0.612),
            2: (0.902, 0.878, 0.823),
        }
        txt = "This is a medium severity defect. Please take action soon."
        view_report["severity"] = "Medium"
    else:
        c.setFillColorRGB(159 / 255, 192 / 255, 137 / 255)

        colorscheme = {
            1: (209 / 255, 223 / 255, 210 / 255),
            2: (121 / 255, 180 / 255, 176 / 255),
        }
        txt = "This is a low severity defect. Please take action when possible."
        view_report["severity"] = "Low"

    c.setStrokeColor(colors.black)
    c.rect(50, height - 115, 500, 30, fill=True)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(110, 685, txt)

    c.setFillColorRGB(*colorscheme[1])
    c.rect(50, height - 160, 500 / 2, 30, fill=True)
    c.setFillColorRGB(*colorscheme[2])
    c.rect(500 / 2, height - 160, 300, 30, fill=True)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(60, height - 150, "Type")
    c.drawString(500 / 2 + 10, height - 150, "Description")

    def draw_metadata_section(c, title, value, y_position, height):
        
        c.setFont("Helvetica", 14)
        c.setFillColorRGB(0, 0, 0)
        title_x_position = 50
        value_x_position = 260
        line_width = 550 - value_x_position

        c.drawString(title_x_position, y_position, title)
        c.line(50, y_position - 5, 250, y_position - 5)
        
        current_y = y_position
        line = ""
        
        c.line(250, y_position - 5, 550, y_position - 5)
        words = value.split(' ')
        
        # word wrapping
        for word in words:
            # Test the width of the line with the new word
            test_line = line + word + ' '
            text_width = c.stringWidth(test_line, "Helvetica", 14)
            
            if text_width > line_width:
                c.drawString(value_x_position, current_y + 10, line.strip())
                current_y -= 3  
                line = word + ' ' 
            else:
                line = test_line 
        
        if line:
            c.drawString(value_x_position, current_y, line.strip())

    draw_metadata_section(
        c,
        "Defect Reference No.:",
        view_report["name"].split(".")[0],
        height - 185,
        height,
    )
    draw_metadata_section(
        c, "Type of Inspection:", view_report["ins_type"], height - 215, height
    )
    draw_metadata_section(
        c, "Type of Road/Footpath:", view_report["road_type"], height - 245, height
    )
    draw_metadata_section(c, "Defect Type:", view_report["type"], height - 275, height)
    draw_metadata_section(
        c, "Location - Longitude:", str(view_report["longitude"]), height - 305, height
    )
    draw_metadata_section(
        c, "Location - Latitude:", str(view_report["latitude"]), height - 335, height
    )
    draw_metadata_section(
        c, "Inspected By:", view_report["inspector"], height - 365, height
    )
    draw_metadata_section(
        c, "Severity:", str(view_report["severity"]), height - 395, height
    )

    c.line(500 / 2, height - 400, 500 / 2, height - 160)

    # Image section
    image_path = view_report["image"].replace("_defect", "_legend_defect")
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(50, 52, 500, 320)
    
    try:
        c.drawImage(
            image_path,
            50,
            height - 740,
            width=500,
            height=320
        )
    except FileNotFoundError:
        # Handle the case where the image file is missing
        print("Image file not found.")
        c.drawCentredString(width/2, 200, "Image not available")

    except Exception as e:
        # Handle other exceptions, like incorrect path or unsupported image format
        print("An error occurred:", e)
        c.drawCentredString(width/2, 200, "Image not available")

    return c


def separate_pavement_issues(defects):
    crack_terms = [
        "alligator crack",
        "peel off with cracks",
        "rigid pavement crack",
        "single crack",
        "transverse crack",
    ]
    damage_terms = ["damaged kerb", "peeling off premix", "wearing course peeling off"]
    spillage_terms = ["paint spillage"]
    other_terms = ["pothole with crack", "ravelling"]

    issues = ", ".join(defects)
    issues = issues.split(", ")

    all_categories = set()
    for issue in issues:
        if issue in crack_terms:
            all_categories.add("Crack")
        elif issue in damage_terms:
            all_categories.add("Damage")
        elif issue in spillage_terms:
            all_categories.add("Spillage")
        elif issue in other_terms:
            all_categories.add("Other")
        else:
            all_categories.add("Other")

    all_categories = ", ".join(all_categories)

    return all_categories


def map_types_to_bboxes(defect_types, bboxes):
    """
    Maps defect types to their corresponding bounding boxes.
    Ensures grouped defect types (like 'Faded Kerb (1M)' and 'Faded Kerb (2M)') share a combined bounding box.
    """
    defect_mapping = {}

    for defect, bbox in zip(defect_types, bboxes):
        normalized_defect = defect.split(" (")[0].title()  # Remove size (e.g., "(1M)")
        
        if normalized_defect in defect_mapping:
            # Merge bounding boxes by taking min/max coordinates
            existing_bbox = defect_mapping[normalized_defect]
            x_min = min(existing_bbox[0], bbox[0])
            y_min = min(existing_bbox[1], bbox[1])
            x_max = max(existing_bbox[2], bbox[2])
            y_max = max(existing_bbox[3], bbox[3])
            defect_mapping[normalized_defect] = [x_min, y_min, x_max, y_max]
        else:
            defect_mapping[normalized_defect] = bbox

    return defect_mapping


def template1(c, view_report):
    defect_name = view_report['defect_type'].replace(" ", "_")
    print(view_report)
    # for repeat in view_report["type"]:
    #     if repeated_defects(repeat, view_report["road"]) == "Yes":
    #         repeat_defects = "Yes"
    #         break
    #     else:
    #         repeat_defects = "No"

    width, height = letter
    categories = separate_pavement_issues(view_report["defect_type"])

    # unique_types = set()
    # for issue in view_report["type"]:
    #     if issue.startswith("Faded Kerb"):
    #         unique_types.add("Faded Kerb")
    #     else:
    #         unique_types.add(issue)

    # issues = ", ".join(unique_types)

    if view_report["severity"] == 3:
        view_report["severity"] = "High"
    elif view_report["severity"] == 2:
        view_report["severity"] = "Medium"
    else:
        view_report["severity"] = "Low"
    print('\n',"report img",view_report["image"])
    print(view_report["image"][-5:]!='t.jpg')
    if view_report["image"][-5:]!='t.jpg':
        view_report["image"]=view_report["image"].replace(".jpg", "_defect.jpg")

    print('\n',"report img",view_report["image"])  
    c.setFont("Helvetica-Bold", 12)
    c.setLineWidth(2)
    c.drawString(40, height - 45, "Contract XXX")
    c.drawCentredString(width / 2.0, height - 60, "Defect Record Sheet")
    c.rect(40, height - 760, width - 80, height - 100, fill=False)
    c.line(70, height - 760, 70, height - 68)
    c.drawString(50, height - 85, "A")
    c.line(40, height - 585, width - 40, height - 585)
    c.drawString(50, height - 602, "B")
    c.line(40, height - 695, width - 40, height - 695)
    c.drawString(50, height - 712, "C")

    c.setFont("Helvetica", 12)
    c.setLineWidth(1)

    # Metadata Section A, repeat_defects
    c.setFillColorRGB(1.0, 0.0, 0.0)
    c.drawString(180, height - 100, view_report["name"])
    c.drawCentredString(305, height - 130,view_report["defectRepeatedValue"])
    c.drawString(
        75, height - 518, "Defects reported to DRC / RARL / RIA / other agencies on:"
    )

    c.setFillColorRGB(0.0, 0.0, 0.0)
    c.drawString(75, height - 100, "Defect Ref No:")
    c.line(180, height - 105, 340, height - 105)
    c.drawString(75, height - 130, "Repeated Defect: (Yes/No):")
    c.line(270, height - 135, 340, height - 135)
    c.drawString(400, height - 130, "Severity:")
    c.drawCentredString(510, height - 130, view_report["severity"])
    c.line(470, height - 135, 550, height - 135)
    c.drawString(400, height - 100, "Date/Time:")
    c.drawCentredString(510, height - 100, str(view_report["ins_date"]))
    c.line(470, height - 105, 550, height - 105)
    c.drawString(75, height - 160, "Type of Road/Footpath/Facilities:")
    c.drawCentredString(335, height - 160, view_report["road_type"])
    c.line(270, height - 165, 400, height - 165)

    def draw_metadata_section(c, title, value, y_position, height):

        c.setFont("Helvetica", 12)
        title_x_position = 75
        value_x_position = 210
        line_width = 550 - value_x_position
        

        c.drawString(title_x_position, y_position, title)
        
        current_y = y_position
        line = ""
        
        c.line(value_x_position, y_position - 5, 550, y_position - 5)
        words = value.split(' ')
        
        # word wrapping
        for word in words:
            # Test the width of the line with the new word
            test_line = line + word + ' '
            text_width = c.stringWidth(test_line, "Helvetica", 12)
            
            if text_width > line_width:
                c.drawString(value_x_position, current_y + 10, line.strip())
                current_y -= 3  
                line = word + ' ' 
            else:
                line = test_line 
        
        if line:
            c.drawString(value_x_position, current_y, line.strip())
        

    draw_metadata_section(
        c, "Location / Landmark:", view_report["road"].title(), height - 190, height
    )
    draw_metadata_section(c, "Type of Asset:", str(categories), height - 220, height)
    draw_metadata_section(c, "Description:", view_report["defect_type"], height - 250, height)
    draw_metadata_section(c, "Quantity:", view_report["quantity"], height - 280, height)
    draw_metadata_section(
        c, "Measurement:", view_report["measurement"], height - 310, height
    )
    draw_metadata_section(
        c, "Cause of Defect:", view_report["cause"], height - 340, height
    )
    draw_metadata_section(
        c, "Recommendation:", view_report["recommendation"], height - 370, height
    )
    draw_metadata_section(
        c, "Others/Remarks:", view_report["remarks"], height - 400, height
    )

    c.drawString(75, height - 440, "Inspected By:")
    c.line(210, height - 440, 350, height - 440)
    c.line(400, height - 440, 550, height - 440)
    c.drawCentredString(280, height - 435, view_report["inspector"])
    c.drawCentredString(280, height - 452, "Name")
    c.drawCentredString(475, height - 452, "Signature")

    c.drawString(75, height - 480, "Supervised By:")
    c.line(210, height - 480, 350, height - 480)
    c.line(400, height - 480, 550, height - 480)
    c.drawCentredString(280, height - 475, view_report["supervisor"])
    c.drawCentredString(280, height - 492, "Name")
    c.drawCentredString(475, height - 492, "Signature")

    c.drawString(75, height - 545, "Reported Via:")
    c.drawString(190, height - 545, "Method / Agency / Date / Time:")
    c.drawString(370, height - 545, view_report["via"])
    c.line(370, height - 550, 550, height - 550)
    c.drawString(75, height - 575, "Acknowledgement:")
    c.drawString(190, height - 575, "Method / Date / Time:")
    c.drawString(370, height - 575, view_report["acknowledgement"])
    c.line(370, height - 580, 550, height - 580)

    # Metadata Section B
    c.drawString(75, height - 602, "(For LTA Use)")
    c.drawString(75, height - 625, "Defects Verified by:")
    c.line(210, height - 625, 550, height - 625)
    c.drawString(250, height - 639, "Name")
    c.drawString(350, height - 639, "Signature")
    c.drawString(480, height - 639, "Date")
    c.drawString(75, height - 660, "Instructions:")
    c.line(210, height - 660, 550, height - 660)
    c.drawString(75, height - 690, "WSO No.:")
    c.line(210, height - 690, 550, height - 690)

    # Metadata Section C
    c.drawString(75, height - 712, "(For contractor's acknowledgement)")
    c.drawString(75, height - 738, "Acknowledged &")
    c.drawString(75, height - 752, "Received by:")
    c.line(210, height - 738, 550, height - 738)
    c.drawString(250, height - 752, "Name")
    c.drawString(350, height - 752, "Signature")
    c.drawString(480, height - 752, "Date")

    c.showPage()

    # Page 2
    c.setFont("Helvetica-Bold", 12)
    c.setLineWidth(2)
    c.drawCentredString(width / 2.0, height - 40, "Defect Record Sheet")
    c.rect(40, height - 730, width - 80, height - 90, fill=False)
    c.line(40, height - 45, width - 40, height - 45)
    c.line(40, height - 75, width - 40, height - 75)
    c.line(40, height - 90, width - 40, height - 90)
    c.line(40, height - 400, width - 40, height - 400)
    c.line(40, height - 415, width - 40, height - 415)

    # Map Section
    c.setLineWidth(1)
    text = "Sketch"
    text_width = c.stringWidth(text)
    c.drawCentredString(width / 2.0, height - 87, text)
    mapzoom = 15
    print("\nwidth=",width,"\nheight=",height)
    try:
        # map_url = f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/pin-s({view_report['longitude']},{view_report['latitude']})/{view_report['longitude']},{view_report['latitude']},{mapzoom}/800x600?access_token=pk.eyJ1IjoiaGF6ZW0tcGF0ZWwiLCJhIjoiY2xkdWF6ejE3MDQweTNvbXBheHZ0Z2tsdSJ9.TXwOfeEyMV29Qy8V7y-uwQ"
        map_io = generate_static_map(view_report['latitude'], view_report['longitude'], width=512, height=512)

        if map_io:
            # Convert BytesIO to ImageReader
            map_image = ImageReader(map_io)
            # with open("debug_map.png", "wb") as f:
            #     f.write(map_io.getbuffer())
            # Draw the image into the PDF
            c.drawImage(map_image, 100, height - 398, width=width - 200, height=305)
        else:
            print("Failed to fetch map image")
    except FileNotFoundError:
        c.drawString(250, height - 240, "Sketch not available")
    except Exception as e:
        print("An error occurred while drawing the map:", repr(e))
        c.drawString(250, height - 240, "Sketch not available")

    underline_y = height - 88
    c.line((width - text_width) / 2, underline_y, (width + text_width) / 2, underline_y)

    c.drawCentredString(width / 2.0, height - 413, "Photographs")
    underline_y = height - 413
    c.line((width - text_width) / 2, underline_y, (width + text_width) / 2, underline_y)
    c.setFont("Helvetica", 12)

    c.drawString(45, height - 70, "Location & Photographs")
    c.drawString(320, height - 70, "Defect Ref No:")
    c.drawString(420, height - 70, view_report["name"])

    try:
        c.drawImage(
            view_report["image"].replace("_defect", "_"+defect_name+"_defect"),
            41,
            height - 730,
            width=width - 82,
            height=height - 478,
        )
    except FileNotFoundError:
        c.drawCentredString(310, height - 580, "Image not available")
    except Exception as e:
        print("An error occurred:", e)
        c.drawCentredString(310, height - 580, "Image not available")

    c.showPage()

    # Page 3
    c.setLineWidth(2)
    c.rect(40, height - 382, width - 80, height / 2 - 68, fill=False)
    c.line(40, height - 212, width - 40, height - 212)
    c.line(width / 2, height - 371, width / 2, height - 53)
     
    # Draw the annotated image
    try:
        c.drawImage(
            view_report["image"].replace("_defect", "_"+defect_name+"_defect"),
            41,
            height - 211,
            width=width / 2 - 42,
            height=156,
        )
    except FileNotFoundError:
        c.drawString(120, height - 142, "Image not available")
    except Exception as e:
        print("An error occurred:", e)
        c.drawString(120, height - 142, "Image not available")

    # Draw the original image
    try:
        c.drawImage(
            view_report["image"].replace("_defect", ""),
            307,
            height - 211,
            width=width / 2 - 42,
            height=156,
        )
    except FileNotFoundError:
        c.drawString(390, height - 142, "Image not available")
    except Exception as e:
        print("An error occurred:", e)
        c.drawString(390, height - 142, "Image not available")

    # Draw the cropped image
    try:
        img = Image.open(view_report["image"].replace("_defect", "_"+defect_name+"_defect"))
        bboxes_set = []
        for bbox_str in view_report["filtered_bbox"]:
            # Remove extra characters and split into numbers
            numbers = bbox_str.replace("[", "").replace("]", "").split(",")
            # Convert each number to float and then to int
            bbox_list = [int(float(num.strip())) for num in numbers]
            bboxes_set.append(bbox_list)
        print(bboxes_set)
        bbox_len = len(bboxes_set)
        height_cropped = height - 369

        # if more than 6 defects found, display only the first 6 unique defects
        if len(view_report["defect_type"]) > ConfigData.NO_OF_DEFECTS_SHOWN:
            print(f"More than {ConfigData.NO_OF_DEFECTS_SHOWN} defects found")
            print("Displaying only the first 6 unique defects")
            type_bbox_mapping = map_types_to_bboxes(view_report["defect_type"], bboxes_set)
            print(type_bbox_mapping)
            for i, (defect_type, bbox) in enumerate(type_bbox_mapping.items()):
                x_min, y_min, x_max, y_max = bbox

                # Drawing on image
                draw = ImageDraw.Draw(img)
                draw.rectangle([x_min, y_min, x_max, y_max], outline="red", width=3)
                roi = img.crop((x_min - 100, y_min - 100, x_max + 100, y_max + 100))

                cropped_img_path = f"cropped_image{i}.jpg"
                roi.save(cropped_img_path)

                if i % 2 == 0:
                    x_pos = 41
                else:
                    x_pos = 307

                # Draw the image and text on the canvas
                c.drawImage(
                    cropped_img_path,
                    x_pos,
                    height_cropped,
                    width=width / 2 - 42,
                    height=156,
                )

                # c.drawString(x_pos + 1, height_cropped - 11, "Defect: " + defect_type)
                c.line(40, height_cropped - 14, 40, height - 317)
                c.line(572, height_cropped - 14, 572, height - 317)
                c.line(width / 2, height_cropped - 14, width / 2, height - 317)
                c.line(40, height_cropped - 14, 572, height_cropped - 14)

                if i % 2 != 0:
                    height_cropped -= 170

                # Remove the temporary cropped image file
                os.remove(cropped_img_path)

                if os.path.exists(cropped_img_path):
                    print("File not removed successfully")

        else:
            for i, bbox in enumerate(bboxes_set[:bbox_len]):
                x_min, y_min, x_max, y_max = bbox

                draw = ImageDraw.Draw(img)
                draw.rectangle([x_min, y_min, x_max, y_max], outline="red", width=3)
                roi = img.crop((x_min - 100, y_min - 100, x_max + 100, y_max + 100))

                cropped_img_path = f"cropped_image{i}.jpg"
                roi.save(cropped_img_path)

                if i % 2 == 0:
                    x_pos = 41
                else:
                    x_pos = 307

                c.drawImage(
                    cropped_img_path,
                    x_pos,
                    height_cropped,
                    width=width / 2 - 42,
                    height=156,
                )

                # c.drawString(
                #     x_pos + 1, height_cropped - 11, "Defect: " + view_report["type"][i]
                # )
                c.line(40, height_cropped - 14, 40, height - 317)
                c.line(572, height_cropped - 14, 572, height - 317)
                c.line(width / 2, height_cropped - 14, width / 2, height - 317)
                c.line(40, height_cropped - 14, 572, height_cropped - 14)

                if i % 2 != 0:
                    height_cropped -= 170

                # Remove the temporary cropped image file
                os.remove(cropped_img_path)

                if os.path.exists(cropped_img_path):
                    print("File not removed successfully")

    except FileNotFoundError:
        c.drawString(120, height - 300, "Image not available")
    except Exception as e:
        print("An error occurred:", e)
        c.drawString(120, height - 300, "Image not available")

    return c


def view_report(temp_file):
    webbrowser.open(temp_file)
    while not os.path.exists(temp_file):
        time.sleep(0.1)
    # os.remove(temp_file)


# def generate_report(report_data, template, placeholder):
#     """
#     Generates a PDF report based on the given report data and template,
#     and saves it to the specified filename.
#     """

#     report_data["type"] = [item.title() for item in report_data["type"]]
#     name = report_data["name"] + ".pdf"

#     if placeholder == "temp":
#         with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
#             c = canvas.Canvas(temp_file, pagesize=letter)
#             if template == "2":
#                 c = template2(c, report_data)
#             elif template == "3":
#                 c = template3(c, report_data)
#             else:
#                 c = template1(c, report_data)
#             c.save()

#         print("Report generated")
#         print(temp_file.name)

#         return temp_file.name

#     elif placeholder == "download":
#         if not os.path.exists(os.path.abspath("Reports")):
#             os.makedirs("Reports")
#             print("Reports directory created")

#         path = os.path.abspath("Reports")
#         batchname = report_data["image"].split("\\")[-2]
#         batchfolder = os.path.join(path, batchname)

#         if not os.path.exists(batchfolder):
#             os.makedirs(batchfolder)
#             print("Batch directory created")

#         batchfolder = os.path.join(batchfolder, name)
#         print(batchfolder)

#         with open(batchfolder, "wb") as pdf_file:
#             c = canvas.Canvas(pdf_file, pagesize=letter)
#             if template == "2":
#                 c = template2(c, report_data)
#             elif template == "3":
#                 c = template3(c, report_data)
#             else:
#                 c = template1(c, report_data)
#             c.save()

#         print("Report generated")
#         print(f"PDF saved to: {batchfolder}")

#         return batchfolder
def generate_report(report_data, defect_type, template, placeholder):
    """
    Generates separate PDF reports for each defect type in the report data
    and saves them to the specified filenames.
    """
    # Capitalize defect types
    # report_data["type"] = [item.split(" (")[0].title() for item in report_data["type"]]
    
    # # Get unique defect types
    # unique_types = set(report_data["type"])
    
    # Report directory setup
    if placeholder == "download":
        if not os.path.exists(os.path.abspath("Reports")):
            os.makedirs("Reports")
            print("Reports directory created")
        
        path = os.path.abspath("Reports")
        batchname = report_data["image"].split("\\")[-2]
        # batchname=[]
        batchfolder = os.path.join(path, batchname)
        
        if not os.path.exists(batchfolder):
            os.makedirs(batchfolder)
            print("Batch directory created")
    else:
        batchfolder = tempfile.gettempdir()

    # generated_reports = []  # List to store the paths of generated reports

    # Generate a report for each defect type
    # for defect_type in unique_types:
        # Filter data for the current defect type
        # indices = [i for i, d in enumerate(report_data["type"]) if d == defect_type]
        # filtered_bbox = [report_data["bbox"][i] for i in indices]
        
        # defect_specific_data = {
        #     **report_data,
        #     "defect_type": defect_type,
        #     "filtered_bbox": filtered_bbox,
        # }

        # Set report name
    defect_name = defect_type.replace(" ", "_")
    report_name = f"{report_data['name']}_{defect_name}.pdf"
    report_path = os.path.join(batchfolder, report_name)

    # Create the PDF
    with open(report_path, "wb") as pdf_file:
        c = canvas.Canvas(pdf_file, pagesize=letter)
        if template == "2":
            c = template2(c, report_data)
        elif template == "3":
            c = template3(c, report_data)
        else:
            c = template1(c, report_data)
        c.save()

    print(f"Report generated for {defect_type}: {report_path}")
    # generated_reports.append(report_path)

    return report_path  # Return the list of generated report paths

def add_new_tags(report_id, tags):
    """
    Adds new tags to the database for a specific report.
    """
    
    tags = tags.strip().title()
    tags_list = tags.split(",") if tags else []

    report = db.report.find_one({"reportID": report_id})
    
    if report:
        existing_tags = report.get("tags", "")
        existing_tags_list = existing_tags.split(",") if existing_tags else []

        existing_tags_list = [tag.strip().title() for tag in existing_tags_list]

        # Add new tags if they do not already exist
        new_tags = [tag for tag in tags_list if tag and tag not in existing_tags_list]
        
        if new_tags:
            updated_tags_list = existing_tags_list + new_tags
            updated_tags = ", ".join(updated_tags_list)
            db.report.update_one(
                {"reportID": report_id},
                {"$set": {"tags": updated_tags}},
                upsert=True
            )
            return "Tags added successfully"
        else:
            return "Tags already exist"
    else:
        return "Report not found"

