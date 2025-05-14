# ------------------
# Description
# ------------------
# This file contains the functions for the display settings of layers in QGIS

# ------------------
# Imports
# ------------------
from PyQt5.QtGui import *
import processing
from osgeo import ogr
from qgis.core import QgsVectorLayer, QgsProject, QgsAction
from qgis.utils import iface

# ------------------
# Functions
# ------------------
# ----------------------------
# set_symbol_color function
# ----------------------------
def set_symbol_color(layer_name, red, green, blue):
    symbol = layer_name.renderer().symbol()
    symbol.setColor(QColor.fromRgb(red, green, blue))
    symbol.setSize(5)
    layer_name.triggerRepaint()

    # Refresh layer symbology in layer panel
    iface.layerTreeView().refreshLayerSymbology(layer_name.id())

# ----------------------------
# create_vector_layer function
# ----------------------------
def create_vector_layer(layer_name, geodata, symbolColor, grp = False, grpName = None):
    # Create vector layer
    layer = QgsVectorLayer(geodata, layer_name, "ogr")
    if grp:
         # Add Map layer
        QgsProject.instance().addMapLayer(layer, False) 
        root = QgsProject.instance().layerTreeRoot()
        # Add to Group
        root.findGroup(grpName).addLayer(layer)
    else:
         # Add Map layer
        QgsProject.instance().addMapLayer(layer) 
    # Set symbol color, * is to unpack the tuple
    set_symbol_color(layer, *symbolColor)

    return layer
    
# ---------------------
# select_layer function
# ---------------------
# Selects specific layer in qgis project
def select_layer(layer_name, group_name):
    # Access current qgis project instance
    root = QgsProject.instance().layerTreeRoot() # Retrieve root of layer tree
    group = root.findGroup(group_name)
    if group is not None:
        for child in group.children():
            if child.name() == layer_name:
                # Set as active layer
                iface.setActiveLayer(child.layer())

# -------------------
# add_action function
# -------------------
# Add action in qgis
def add_action(action_manager, action_name):
    action_manager.addAction(action_name)
    action_manager.setDefaultAction("Canvas", action_name.id())

# -------------------------
# set_action_scope function
# -------------------------
# Set action scope in qgis
def set_action_scope(action_name):
    my_scopes = {"Canvas", "Feature"}
    action_name.setActionScopes(my_scopes)

# ------------------------
# set_action_html function
# ------------------------
def set_action_html(layerObject, videoUrl, defectCondition = False, colorCondition = (0, 0, 255)):
    image_url = '[% "OImagePath" %]' 

    # Add Map Action to open Linked Video
    actionManager = layerObject.actions()
    action = QgsAction(QgsAction.OpenUrl, "View Inspection Footage", videoUrl)
    set_action_scope(action)
    add_action(actionManager, action)

    # Add Map Action to open Original Image
    action = QgsAction(QgsAction.OpenUrl, "View Image", image_url)
    set_action_scope(action)
    add_action(actionManager, action)

    # Set HTML Content    
    # Add HTML Map Tip
    image_file = r"file:///" + image_url
    html_style = r"<style> table {border: 1px solid black;} table th, table td {border: 5px solid black;} table th {padding: 0.5rem;} img {width: 350; height: 250;}</style>"
    original_image_html = image_file + r'"></td>'
    html_str_end = r'</tr></table>'
    # If Non-Defect
    html_str_start =  f'<table rules="all"><tr><th style="color: rgb{colorCondition};">Defect: [% "Type" %]</th></tr><tr><td><img src="'
    html_body = original_image_html

    # Add additional defect if feature contains defect
    if defectCondition:
        # QGIS Aggregate -- Prep bouding image url: aggregate OImagePath to add "_defect" before file extension e.g. jpg/jpeg/png
        bounding_image_url = '[% substr("OImagePath", 1, strpos("OImagePath", \'.\') - 1) || \'_defect\' || substr("OImagePath", strpos("OImagePath", \'.\'), length("OImagePath")) %]'

        actionDefect = QgsAction(QgsAction.OpenUrl, "View Bounding Image", bounding_image_url)
        # Action is available on canvas & feature interaction
        set_action_scope(actionDefect)
        # Add action
        add_action(actionManager, actionDefect)

        # Comparison HTML Table between Original Image & Bounding Image
        html_str_start = r'<table rules="all"><tr><th colspan=2 style="color: red; font-size: larger; text-transform: capitalize;">Defect: [% "Type" %]</th></tr><tr><th>Original Image</th><th>Bounding Image</th></tr><tr><td><img src="'
        bouding_image_file = r"file:///" +  bounding_image_url
        bounding_image_html= r'<td><img src="' + bouding_image_file + r'"></td>'
        html_body = original_image_html + bounding_image_html
    
    # Set Map Tip Template
    layerObject.setMapTipTemplate(html_style + html_str_start + html_body + html_str_end)