import cv2
import os
from flask import Flask, jsonify, send_from_directory, Blueprint
import requests
from PIL import Image
import io
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


# from engines import drainage

current_path = os.path.abspath(__file__)
APP_FOLDER = os.path.abspath(os.path.join(current_path, "../../../"))
VIDEO_FOLDER = os.path.join(APP_FOLDER, 'uploads')
UPLOAD_FOLDER = os.path.join(APP_FOLDER, 'upload_frames')
UPLOAD_DEFECTS_FOLDER = os.path.join(APP_FOLDER, 'upload_frames_defects')
REPORT_FOLDER = os.path.join(APP_FOLDER, 'reports')

def create_report(frame_defect_filepath, video_filename, defect_count):
    # pdf1 = open(f'{REPORT_FOLDER}\template\template.pdf', 'rb')
    pdf1 = open(os.path.join(REPORT_FOLDER, 'template\\template.pdf'), 'rb')
    pdf2 = open(create_image_pdf(os.path.join(REPORT_FOLDER, 'template\\temp.pdf'), frame_defect_filepath), 'rb')

    # Create PDF reader objects
    reader1 = PyPDF2.PdfReader(pdf1)
    reader2 = PyPDF2.PdfReader(pdf2)

    # Create a PDF writer object to write the combined output
    writer = PyPDF2.PdfWriter()

    # Add pages from the first PDF
    for page in reader1.pages:
        writer.add_page(page)

    # Add pages from the second PDF
    for page in reader2.pages:
        writer.add_page(page)

    report_path = os.path.join(REPORT_FOLDER, video_filename, f'{video_filename}_{defect_count}.pdf')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    # Create an output file and write the combined content
    with open(report_path, 'wb') as output_pdf:
        writer.write(output_pdf)

    # Close the original PDF filesjfkjsf
    pdf1.close()
    pdf2.close()
    
def create_image_pdf(pdf_file, frame_defect_filepath):
    c = canvas.Canvas(pdf_file, pagesize=letter)

    x_position = 50  # X coordinate for the image
    y_position = 550 # Y coordinate for the image
    image_width = 510  # Width of the image
    image_height = 200  # Height of the image

    c.drawImage(frame_defect_filepath, x_position, y_position, width=image_width, height=image_height)
    c.save()
    
    return pdf_file
    