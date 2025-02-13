from flask import Flask, request, render_template, send_from_directory, jsonify
# from routes.process import process_bp  # Adjust the import according to your structure
import os
from routes import process
import requests
import threading
import urllib.parse

app = Flask(__name__)

# Set the allowed extensions and upload folder
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mkv', 'mov', 'flv', 'wmv'}

current_path = os.path.abspath(__file__)
APP_FOLDER = os.path.abspath(os.path.join(current_path, "../../"))
VIDEO_FOLDER = os.path.join(APP_FOLDER, 'uploads')
UPLOAD_FOLDER = os.path.join(APP_FOLDER, 'upload_frames')
UPLOAD_DEFECTS_FOLDER = os.path.join(APP_FOLDER, 'upload_frames_defects')
REPORT_FOLDER = os.path.join(APP_FOLDER, 'reports')

# Check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clear_folder(folder_path):
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for filename in files:
            file_path = os.path.join(root, filename)
            os.remove(file_path)
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            os.rmdir(dir_path)
            
# Route to handle file upload form
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<report_folder>/<filename>')
def serve_report(report_folder, filename):
    report_folder = urllib.parse.unquote(report_folder)
    filename = urllib.parse.unquote(filename)
    return send_from_directory(report_folder, filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    print(APP_FOLDER)
    print(VIDEO_FOLDER)
    if 'video' not in request.files:
        return 'No file part', 400

    video = request.files['video']
    
    if video and allowed_file(video.filename):
        filename = os.path.join(VIDEO_FOLDER, video.filename)
        video.save(filename)
        # print(filename)
        
        if video.filename == '':
            return 'No selected file', 400
        
        process.start_upload_file(video.filename)
        
        clear_folder(VIDEO_FOLDER)
        clear_folder(UPLOAD_FOLDER)
        clear_folder(UPLOAD_DEFECTS_FOLDER)
        
        if os.path.exists(os.path.join(REPORT_FOLDER, video.filename)):
            report_folder = os.path.join(REPORT_FOLDER, video.filename)
            # report_folder = r'C:\Y2_Sem2\INC stuff\application\reports\template'
            os.makedirs(report_folder, exist_ok=True)
            report_files = [f for f in os.listdir(report_folder) if f.endswith('.pdf')]
            # print(report_folder)
            # print(os.listdir(report_folder))
            return render_template('index.html', report_files = report_files,
                               report_folder = report_folder)
        else:
            return render_template('index.html', report_folder=None, report_files = None)
        
    else:   
        return 'Invalid file type. Only video files are allowed.', 400


@app.route('/test', methods=['GET'])
def test():
    response = requests.get('http://localhost:5009/api')
    return response.text

if __name__ == '__main__':
    app.run(debug=True, port=5008)
    

            
