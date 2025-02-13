@echo off
echo Current Working Directory: %cd%
echo 

echo Starting Flask applications...
echo 

call application\env\Scripts\activate
set FLASK_APP=application\apps\app.py
set FLASK_ENV=development

start cmd /k application\apps\engines\run_drain.bat
@REM call application\env\Scripts\activate
python application\apps\app.py