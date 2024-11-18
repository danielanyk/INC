# ------------------
# Imports
# ------------------
import os
import csv
import time
import tensorflow as tf
import numpy as np
import subprocess

# Preprocessing Data
from tensorflow.keras.preprocessing.image import load_img, img_to_array

# Building CNN Model
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv2D, BatchNormalization, ReLU, MaxPooling2D, Flatten, Dense

from flask import Flask, request, jsonify
from flask_pymongo import PyMongo

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/FYP"
mongo = PyMongo(app)
# db = mongo.db

# --------------------------------------
# Initializes Flask Application Instance
# --------------------------------------
app = Flask(__name__)

# ------------------
# Initialize Model
# ------------------
model = None

# Model Scores CSV file with weights file info
history_file = r".\apps\home\Engines\model_scores.csv"

if os.path.exists(history_file):
    print("Checking weights from history file")
    with open(history_file, mode='r') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        
        if rows:

            # Initialize variables to store the row with the highest accuracy
            max_accuracy_row = rows[0]
            max_accuracy = float(rows[0]['accuracy'])

            # Iterate over the rows to find the one with the highest accuracy
            for row in rows:
                current_accuracy = float(row['accuracy'])
                if current_accuracy > max_accuracy:
                    max_accuracy = current_accuracy
                    max_accuracy_row = row
            
            # Extract and store information from the row with the highest accuracy
            weights_file_name = max_accuracy_row['weights_file_name']
            print(weights_file_name)
else:
    weights_file_name = "sev_classifier_patience_10.h5"

default_weights_path = f"apps/home/Engines/epoch/{weights_file_name}" # Weights checkpoint [File path to be changed]

# ------------------
# Endpoints
# ------------------
# -------------------------------------
# Forcibly terminate the backend server
# -------------------------------------
@app.route("/kill_backend")
def kill_backend():
    os.kill(os.getpid(), 9)  # Send SIGKILL to the current process
    return jsonify("Server is terminating...")

# ------------------
# Load Model
# ------------------
@app.route("/api/load_model_severityAssessment", methods=["POST"])
def load_model(weights_path=default_weights_path):
    
    global model
    start_time = time.time() # Track duration to load model

    active_directory = "active_learning"
    if not os.path.exists(active_directory):
        os.makedirs(active_directory)
    if not os.path.exists(os.path.join(active_directory, "unedited")):
        os.makedirs(os.path.join(active_directory, "unedited"))
    if not os.path.exists(os.path.join(active_directory, "classified")):
        os.makedirs(os.path.join(active_directory, "classified"))
    if not os.path.exists(os.path.join(active_directory, "classified", "s1")):
        os.makedirs(os.path.join(active_directory, "classified", "s1"))
    if not os.path.exists(os.path.join(active_directory, "classified", "s2")):
        os.makedirs(os.path.join(active_directory, "classified", "s2"))
    if not os.path.exists(os.path.join(active_directory, "classified", "s3")):
        os.makedirs(os.path.join(active_directory, "classified", "s3"))

    # Model Configuration [Question][Check if needs to be a separate configuration file]
    if model is None:
        # Model Architecture
        def create_model(input_shape):
            inputs = Input(shape=input_shape)

            # Conv1
            x = Conv2D(1, (4, 4), strides=(1, 1), padding='valid')(inputs)
            x = BatchNormalization()(x)
            x = ReLU()(x)
            
            # Conv2
            x = Conv2D(50, (2, 2), strides=(1, 1), padding='valid')(x)
            x = BatchNormalization()(x)
            x = ReLU()(x)
            x = MaxPooling2D(pool_size=(3, 3))(x)
            
            # Conv3
            x = Conv2D(50, (3, 3), strides=(2, 2), padding='valid')(x)
            x = BatchNormalization()(x)
            x = ReLU()(x)
            
            # Conv4
            x = Conv2D(50, (61, 61), strides=(1, 1), padding='valid')(x)
            x = BatchNormalization()(x)
            x = ReLU()(x)
            
            # Flatten
            x = Flatten()(x)
            
            # Fully connected layers
            x = Dense(500, activation='relu')(x)
            x = Dense(250, activation='relu')(x)
            
            # Output layer
            outputs = Dense(3, activation='softmax')(x)

            model = Model(inputs=inputs, outputs=outputs)
            return model

        # Initialize Model with configuration & weights
        input_shape = (500, 500, 1)
        model = create_model(input_shape)
        model.load_weights(weights_path)
        print(f"Model loaded in {time.time()-start_time} seconds.")

    return jsonify({"message": f"Model loaded in {(time.time() - start_time):.2f} seconds."})

# ------------------
# Perform Prediction
# ------------------
@app.route("/predictSeverity", methods=["POST"])
def predict():
    # ------------------------------------------------------------------------------------------------------------------------
    # Note: Functions altered under process.py: send_prediction_request(), crop_image(), make_inferences(), detection_import()
    # Changes are marked with the comment '[Team HotPink]' in process.py
    # ------------------------------------------------------------------------------------------------------------------------
    image_path = request.json.get("image_path")
    load_model()
    # Severity Class labels that'll be stored in mongoDB
    class_names = [1, 2, 3]

    # Grayscale Images
    def preprocess_image(image_path, target_size):
        # Load the image in grayscale mode
        img = load_img(image_path, target_size=target_size, color_mode='grayscale')
        # Convert the image to a numpy array
        img_array = img_to_array(img)
        # Normalize the image
        img_array /= 255.0
        # Expand dimensions to match the input shape (1, height, width, channels)
        img_array = np.expand_dims(img_array, axis=0)
        return img_array
    
    # Model Prediction
    def predict_image(model, image_path):
        # Preprocess the image
        input_shape = (500, 500)  # Update this if your model expects a different input shape
        processed_image = preprocess_image(image_path, target_size=input_shape)
        # Make a prediction
        predictions = model.predict(processed_image)
        # Get the predicted class
        predicted_class = np.argmax(predictions, axis=1)[0]
        return predicted_class

    predicted_class = predict_image(model, image_path)
    severity_label = class_names[predicted_class]

    batchCompletionMonitoringHook()

    # As we have One-Hot Encoded the class labels, they are now 0 0 0, 0 1 0, 0 0 1
    return jsonify({"severity": severity_label}) # Returns e.g. {"severity": 1}

# ------------------
# Active Learning 
# ------------------

# Counting number of images in each s1, s2, and s3 subfolder under the "classified" folder
def count_images_in_folder(folder_path):
    return len([name for name in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, name))])

# Gets Latest Batch Status
def get_batch_status(db):
    try:
        # Fetch the latest batch information
        latest_batch = list(db.batch.find().sort('batchID', -1).limit(1))
        if not latest_batch:
            return {'error': 'No batches found'}, 404
        
        # Get the status of the latest batch
        batch_status = latest_batch[0].get('status', 'Unknown') # If no status, it will return "Unknown"
        return {'status': batch_status, 'batch_id': latest_batch[0].get('batchID')}
    
    except Exception as e:
        return {'error': str(e)}, 500
    
def batchCompletionMonitoringHook():

    classified_dir = r".\active_learning\classified\train"

     # Paths to the subfolders
    subfolders = ['s1', 's2', 's3']
    target_count = 200

    # Check if each subfolder has 200 images
    for subfolder in subfolders:
        subfolder_path = os.path.join(classified_dir, subfolder)

        if count_images_in_folder(subfolder_path) < target_count:
            print("Target count of 200 images in each folder has not been met")
            return # Exits the function if either of the subfolders have less than 200 images
    
    # Check the status of the last processed batch
    batch_info = get_batch_status(db)  
    status = batch_info.get('status')

    if status in ["complete", "completed"]:
        print("Latest batch has finished processing, running AL.py")
        # Run AL.py
        subprocess.run(["python", "AL.py"])
    else:
        print("Latest batch has not finished processing")
        
# ------------------
# Clear console
# ------------------
@app.route("/clearConsole", methods=["GET"])
def clear_console():
    os.system('cls')
    return jsonify({"message": "Console cleared."})

# ------------------
# Main Program
# ------------------
if __name__ == "__main__":
    app.run(port=5005, debug = True)