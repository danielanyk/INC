REM Shutdown commands for the servers
REM Close Down Main Flask Server
curl -X POST http://localhost:5000/shutdown

REM Close 4 Engines
curl -X POST http://localhost:5001/shutdown
curl -X POST http://localhost:5002/shutdown
curl -X POST http://localhost:5003/shutdown
curl -X POST http://localhost:5004/shutdown


