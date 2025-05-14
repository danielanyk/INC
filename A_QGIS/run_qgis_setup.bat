@echo off
@REM Purpose: Automatically run python script to setup latest data in layers and dashboard system in QGIS project

@REM !!!!!!!!!!! Set path to QGIS installation (Change accordingly, version yad has is Long Term Release(LTR))
@REM SET "QGIS_PATH=C:\Program Files\QGIS 3.34.5\bin"
SET "QGIS_PATH=C:\Program Files\QGIS 3.38.1\bin"

@REM Get the current working directory to dynamically set directories, shld return C:\Users\....\....\fyp_teampink\A_QGIS
SET "CURRENT_DIR=%CD%"

@REM !!!!!!!!!!! Set path to QGIS installation (Change accordingly, version yad has is Long Term Release(LTR))
SET "QGIS_PATH=C:\Program Files\QGIS 3.38.1\bin"
@REM SET "QGIS_PATH=C:\Users\Hong Yi\OneDrive\A-SCHOOL MATERIAL\polytechnic\2023_S2\Z_INC_XXXXX\ay23s2.inc_teampink\master\tools\bin"
@REM SET "QGIS_PATH=%CURRENT_DIR%\..\QGIS\bin"

@REM Dynamically set Path to Python script (Change accordingly)
SET "SCRIPT_PATH=%CURRENT_DIR%\MongoDB Connection\QGIS Project Setup.py"
ECHO "Script Path: %SCRIPT_PATH%"

@REM Specify data directory to delete, to avoid any error of: GeoJson file is being accessed
SET directory="%CURRENT_DIR%\MongoDB Connection\data"
@REM Check if data directory exists
IF EXIST %directory% (
    @REM Delete directory completely
    rmdir /s /q %directory%
    ECHO Data Directory: %directory% deleted successfully. Continuing...
) ELSE (
    ECHO Data Directory: %directory% does not exist. Continuing...
)

@REM GET DIRECTORY FOR SEVERITY: Output CURRENT_DIR
ECHO "CURRENT_DIR: %CURRENT_DIR%"

@REM GET DIRECTORY FOR SEVERITY: Navigate up from CURRENT_DIR (inside A_QGIS) to TSM-Deploy-3-6-2024
SET "FYP_BASE_PATH=%CURRENT_DIR%\.."
SET "FYP_BASE_PATH=%FYP_BASE_PATH%"

@REM GET DIRECTORY FOR SEVERITY: Output FYP_BASE_PATH
ECHO FYP_BASE_PATH: %FYP_BASE_PATH%

@REM !!!!!!!!!!! Run either one of the commands below, depending on your QGIS version: 
@REM 1. Run QGIS with the Python script
"%QGIS_PATH%\qgis-bin.exe" --code "%SCRIPT_PATH%"

@REM 2. Run QGIS LTR with the project file and the startup script
@REM "%QGIS_PATH%\qgis-ltr-bin.exe" --code "%SCRIPT_PATH%"
