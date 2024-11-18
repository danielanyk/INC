@echo off
echo Starting Flask applications...

REM Starting Flask Run
start cmd /c "flask_run.bat"

REM Starting the 4 Engines
start /b cmd /c ".\apps\home\Engines\engine_raveling.bat"
start /b cmd /c ".\apps\home\Engines\engine_17defects.bat"
start /b cmd /c ".\apps\home\Engines\engine_kerb.bat"
start /b cmd /c ".\apps\home\Engines\engine_severity.bat"
start /b cmd /c ".\apps\home\Engines\engine_paintSpillage.bat"
start cmd /c ".\apps\home\Engines\engine_summarization.bat"


timeout /t 20 /nobreak >nul
echo loading in models
curl -X post http://localhost:5002/api/load_model_17defects

timeout /t 3 /nobreak >nul

curl -X POST http://localhost:5001/api/load_model_raveling

timeout /t 3 /nobreak >nul

curl -X POST http://localhost:5003/api/load_model_kerb

timeout /t 3 /nobreak >nul

curl -X POST http://localhost:5004/api/load_model_paintSpillage

timeout /t 3 /nobreak >nul

curl -X POST http://localhost:5005/api/load_model_severityAssessment

timeout /t 3 /nobreak >nul

curl -X POST http://localhost:5007/api/load_model_llm

echo All applications are running.
	