@echo off
echo Call Starting Up Application
call env\Scripts\activate.bat

echo Successfully activated environment

REM Get local IP address using Python and store it in a variable
for /f "delims=" %%i in ('python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('10.255.255.255', 1)); print(s.getsockname()[0]); s.close()"') do set LOCAL_IP=%%i

echo Detected local IP: %LOCAL_IP%
flask run --no-debugger --no-reload --host=%LOCAL_IP% --port=5000

pause
