# ------------------
# Description
# ------------------
# Purpose: Setup an Empty QGIS Project, afterwards, execute main.py to setup QGIS layers

# ------------------
# Imports
# ------------------
import os
from qgis.core import QgsProject

# ---------------------------------
# Dynamically Prep Data Directories
# ---------------------------------
# Get current directory
current_directory = os.getcwd() # shld be C:\Users\...\...\fyp_teampink\A_QGIS

# -------------------------
# set_project_name function
# -------------------------
def set_project_name():
    # Instantiate QGIS Project
    project = QgsProject.instance()
    
    # Extract the directory path
    directory_path = f'{current_directory}/MongoDB Connection'
    
    # New project name with the same directory path
    new_project_name = os.path.join(directory_path, "Road Inspection Analytics System.qgz")
    
    # Rename and save the project
    project.setFileName(new_project_name)
    project.write()
    print("Project renamed and saved as:", new_project_name)

# ------------------
# Main
# ------------------
current_project = QgsProject.instance()
# Set Project Name
try:
    # Clear current project
    current_project.clear()
    set_project_name()
except Exception as e:
    print(e, "Current project is empty")
    set_project_name()

# ----------------------------------------------------
# Execute main.py: Setup QGIS Layers with MongoDB data
# ----------------------------------------------------
# Define __file__ manually before executing other scripts
main_script_path = os.path.join(current_directory, 'MongoDB Connection', 'main.py')
master_dashboard_setup_path = os.path.join(current_directory, 'MongoDB Connection', 'Master Dashboard Setup.py')

with open(main_script_path) as main_file:
    exec(main_file.read(), {'__file__': main_script_path})

with open(master_dashboard_setup_path) as master_file:
    exec(master_file.read(), {'__file__': master_dashboard_setup_path})
