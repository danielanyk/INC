@echo off
echo Starting Flask applications...

REM Starting Flask Run
start cmd /c "flask_run.bat"


@REM REM Starting the 4 engines
@REM start /b cmd /c ".\apps\home\Engines\engine_raveling.bat"
@REM start /b cmd /c ".\apps\home\Engines\engine_17defects.bat"
@REM start /b cmd /c ".\apps\home\Engines\engine_kerb.bat"
@REM start /b cmd /c ".\apps\home\Engines\engine_severity.bat"
@REM start /b cmd /c ".\apps\home\Engines\engine_paintSpillage.bat"
@REM start cmd /c "C:\Users\DanielYeoh\Downloads\9251-traffic-1\application\run.bat"
@REM start cmd /c ".\apps\home\Engines\engine_summarization.bat"


@REM timeout /t 20 /nobreak >nul
@REM echo loading in models
@REM curl -v -X post http://localhost:5002/api/load_model_17defects

@REM timeout /t 10 /nobreak >nul

@REM curl -v -X POST http://localhost:5001/api/load_model_raveling

@REM timeout /t 10 /nobreak >nul

@REM curl -v -X POST http://localhost:5003/api/load_model_kerb

@REM timeout /t 10 /nobreak >nul

@REM curl -v -X POST http://localhost:5004/api/load_model_paintSpillage

@REM timeout /t 10 /nobreak >nul

@REM curl -v -X POST http://localhost:5005/api/load_model_severityAssessment

@REM timeout /t 10 /nobreak >nul

@REM curl -v -X POST http://localhost:5007/api/load_model_llm

echo All applications are running.
call env\Scripts\activate.bat
set MONGO_URI=mongodb://localhost:27017
REM Starting the autoupload
python apps\home\Autoupload.py
echo All applications are running 2.