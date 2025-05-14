# ------------------
# Description
# ------------------
# Purpose: Setup QGIS Layers, by querying latest data from MongoDB Database

# ------------------
# Imports
# ------------------
from PyQt5.QtGui import *
import os, shutil
import pandas as pd
import geopandas as gpd 
import processing
from qgis.core import QgsProject, QgsRasterLayer, QgsLayerTreeGroup
from qgis.utils import iface
from PyQt5.QtCore import QTimer
import time
time.sleep(0.05) # Stablise execution flow and QGIS environment setup
from functions.mongodb_functions import *
from functions.qgis_functions import *

# ---------------------------------
# Dynamically Prep Data Directories
# ---------------------------------
# Get current directory
current_directory = os.getcwd() # shld be C:\Users\...\...\fyp_teampink\A_QGIS
data_path = f"{current_directory}/MongoDB Connection/data"
inspectionDateData_path = data_path + "/Inspection Dates"
all_defect_path = data_path + "/All Merged"
latestBatchData_path = data_path + "/Latest Batch"

# Double Confirm removal "data" folder inside "MongoDB Connection", because geojson files will be regenerated
try:
    if os.path.exists(data_path):
        shutil.rmtree(data_path)
        print(f'Succesfully removed {data_path}')
    else:
        print(f"{data_path} doesn't exist")
except Exception as e:
    print(e)
# Remake data directory
os.mkdir(data_path)

# ------------------------------------------------------------------------------------------------------
# Set OneMap as Base Canvas via XYZ tile
# Source code: https://gis.stackexchange.com/questions/384000/adding-an-xyz-tile-using-pyqgis-in-pycharm
# ------------------------------------------------------------------------------------------------------
# Load XYZ tile
urlWithParams = 'type=xyz&url=https://www.onemap.gov.sg/maps/tiles/Default_HD/{z}/{x}/{y}.png'
# Create raster layer
xyzTile = QgsRasterLayer(urlWithParams, 'OneMap', 'wms')
xyzTile.isValid()
# Add layer to current project
QgsProject.instance().addMapLayer(xyzTile)
print("OneMap Base Canvas Setup Succesfully")

# ------------------------------
# (1) Inspection Dates
# ------------------------------
# Reference root of layer tree in current qgis project
root = QgsProject.instance().layerTreeRoot()
mygroup = root.insertGroup(0, 'Inspection Dates')
unique_dates_list = get_InspectionDate()
# Change video_url
list_url = r"https://www.dropbox.com/sh/u7t035ijq2kub7w/AAD5OqPXUK3GxnBR_qnhYgu6a/6.%20201010/1.%20Video/20201010_SHIFT_1_S6A_S6B?dl=0&preview=[% file_name %]&subfolder_nav_tracking=1"

# Loop through folders in "Inspection Dates" Directory
for inspectionDate in unique_dates_list:
    # Add sub-groups of Specific Inspection Date
    mygroup.addGroup(inspectionDate)
    inspectionDate_folder = inspectionDateData_path + f'/{inspectionDate}'
    for path, directories, files in os.walk(inspectionDate_folder):
        for file in files:
            if file.endswith(".geojson"):
                # Condition to check if image contains defect
                defect_condition = False
                if len(file.split("_")) > 1:
                    # Extract label of "Defect or "NonDefect"
                    label = file.split("_")[1].split(".")[0]
                    # Define Layer Name
                    layerName = label
                    # Define symbol color
                    if label == 'Defect':
                        # Condition to check if image contains defect
                        defect_condition = True
                        symbolColor = (255, 0, 0)
                    elif label == "NonDefect":
                        symbolColor = (0, 255, 0)
                else:
                    # Define Layer Name
                    layerName = file.replace(".geojson", "")
                    # Define symbol color
                    symbolColor = (0, 0, 255)
                    lastLayerName = layerName

                # Create and Add Vector Layer to Map and Group
                layer = create_vector_layer(layerName, path + f"/{file}", symbolColor, True, inspectionDate)

                # Set Action and HTML
                set_action_html(layer, list_url, defect_condition, symbolColor)

    # Fix order of layers, such that layer with all image points is bottom layer in sub group
    inspection_date_subgroup = mygroup.findGroup(inspectionDate)
    # Find layer node with lastLayerName
    for child in inspection_date_subgroup.children():
        if child.name() == lastLayerName:
            # Move layer node to bottom & set layer name
            inspection_date_subgroup.insertChildNode(-1, child.clone())
            inspection_date_subgroup.removeChildNode(child)
            break
            
print("Inspection Dates Layer Setup Successfully")

# -----------------------------------------------------
# (2) Merge All Defects in Current Project into a Layer
# -----------------------------------------------------
# Reference root of layer tree in current qgis project
root = QgsProject.instance().layerTreeRoot()

# Make All Merged directory
os.mkdir(all_defect_path)

# Collect all "Defect" layers from "Inspection Dates" Group inside a list
all_defect = []
for child in root.findGroup('Inspection Dates').children(): # Child is "D M Y" subgroup
    for subChild in child.children():
        if subChild.name() == 'Defect':
            all_defect.append(subChild.layer())

# Create Combined GeoJSON file
# Load layers
layers = [gpd.read_file(layer.source()) for layer in all_defect]
# Merge features
merged_features = gpd.GeoDataFrame(pd.concat(layers, ignore_index=True))
# Write output
merged_features.to_file(all_defect_path + "/all_defect.geojson", driver='GeoJSON')
# Create and Add Vector Layer to Map
layer = create_vector_layer('All Defects', all_defect_path + "/all_defect.geojson", (255, 0 ,0))
# Set Action and HTML
set_action_html(layer, list_url, True)

print("Merged all defects into a layer successfully")

# ------------------------------
# (3) Latest Batch
# ------------------------------
# Reference root of layer tree in current qgis project
root = QgsProject.instance().layerTreeRoot()
mygroup = root.insertGroup(0, 'Latest Batch')

# Get GeoJSON data
geoJSON_paths = get_latestBatch()
counter = 0
for path in geoJSON_paths:
    layerNames = ["Latest Batch Defects", "Latest Batch Non Defects", "Latest Batch"]
    symbolColor = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    # Create and Add Vector Layer to Map and Group
    layer = create_vector_layer(layerNames[counter], path, symbolColor[counter], True, 'Latest Batch')
    # Set Action and HTML
    set_action_html(layer, list_url, True if counter == 0 else False, symbolColor[counter])
    counter += 1

print("Latest Batch Layer Setup Successfully")

# -------------------------
# (4) Set Final Map
# -------------------------
# Access the project instance
project = QgsProject.instance()
root = project.layerTreeRoot()

# Set active layer
active_layer = None
for layer in root.findLayers():
    if layer.name() == "Latest Batch":
        active_layer = layer.layer()
        print(f"Found active layer: {layer.name()}")
    if layer.name() == "All Defects":
        allDefectLayer = layer.layer()

# Function to zoom into the 'Latest Batch' layer
def zoom_to_layer():
    # Set 'Latest Batch' as active layer
    iface.setActiveLayer(active_layer)
    
    # Ensure the layer is correctly set as active
    if iface.activeLayer() == active_layer:
        print("Successfully set the active layer")
        
        # Zooms in to active layer
        iface.zoomToActiveLayer()
        
        # Refresh map canvas to reflect new extent
        iface.setActiveLayer(allDefectLayer)
        iface.mapCanvas().refresh()
    else:
        print("Failed to set the active layer")

# If 'Latest Batch' layer is detected
if active_layer:
    # Get layer panel tree view
    layerTreeView = iface.layerTreeView()

    # Only set 'OneMap', 'All Defects' & 'Latest Batch' layer to visible
    for child in root.children():
        if child.name() == "All Defects":
            iface.setActiveLayer(child.layer())
            child.setItemVisibilityChecked(True)

        if isinstance(child, QgsLayerTreeGroup):
            if child.name() == "Latest Batch":
                for subgroup in child.children():
                    # Make subgroup invisible
                    subgroup.setItemVisibilityChecked(False)
                    subgroup.setExpanded(False)
                # Collapse "Inspection Dates" group in layer panel view
                child.setExpanded(False)

    # Allow time for layers to fully load before zooming into the layer
    QTimer.singleShot(2000, zoom_to_layer)
else:
    print("Layer 'Latest Batch' not found")

print(f"Finished Map Setup Successfully")