@echo off
@REM Purpose of bat file is to automatically run the python script to setup the dashboard in an existing qgis project

@REM Get the current working directory to dynamically set directories, shld return C:\Users\....\....\fyp_teampink\A_QGIS
SET "CURRENT_DIR=%CD%"

@REM !!!!!!!!!!! Set path to QGIS installation (Change accordingly, version yad has is Long Term Release(LTR))
SET "QGIS_PATH=C:\Program Files\QGIS 3.38.2\bin"
@REM SET "QGIS_PATH=%CURRENT_DIR%\..\QGIS\bin"

@REM Dynamically set Path to QGIS project file 
SET "PROJECT_PATH=%CURRENT_DIR%\MongoDB Connection\Road Inspection Analytics System.qgz"
ECHO Project Path: %PROJECT_PATH%

@REM Dynamically set Path to Python script
SET "SCRIPT_PATH=%CURRENT_DIR%\MongoDB Connection\Master Dashboard Setup.py"
ECHO Script Path: %SCRIPT_PATH%

@REM !!!!!!!!!!! Run either one of the commands below, depending on your QGIS version: 

@REM 1. Run QGIS with the Python script
"%QGIS_PATH%\qgis-bin.exe" --project "%PROJECT_PATH%" --code "%SCRIPT_PATH%"