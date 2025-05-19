Echo Call Starting Up Application
call env\Scripts\activate.bat

echo succcesfully activated environment
flask run --no-debugger --no-reload --host=192.168.0.111 --port=5000
pause