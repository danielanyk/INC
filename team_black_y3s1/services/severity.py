import numpy as np
import cv2
import os
import tensorflow as tf
from tensorflow.keras.layers import Conv2D, BatchNormalization, ReLU, MaxPooling2D, Flatten, Dense, Input
from tensorflow.keras.models import Model
import os
tf.config.optimizer.set_jit(True)
class SeverityEngine:
    def __init__(self):
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "sev_classifier_patience_10.h5"))
        self.model = self.create_model((500, 500, 1))  # Make sure the input shape matches your training config
        self.model.load_weights(model_path)

    def create_model(self, input_shape):
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

        return Model(inputs=inputs, outputs=outputs)

    def predict(self, image_path):
        # Load the image in grayscale
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Resize to match input shape
        img = cv2.resize(img, (500, 500))
        img = img.astype(np.float32) / 255.0  # Normalize to [0, 1]

        # Reshape to (1, 500, 500, 1)
        img = np.expand_dims(img, axis=(0, -1))

        # Run prediction
        predictions = self.model(img, training=False)[0].numpy()
        severity_labels = ["Low", "Moderate", "Severe"]
        return severity_labels[np.argmax(predictions)]
