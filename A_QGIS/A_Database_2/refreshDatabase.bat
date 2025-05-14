@echo off
:: Get the directory of the currently executing script
set scriptDir=%~dp0

:: Run the Node.js script to clear the folder
node "%scriptDir%clearFolder.js"

:: Run the MongoDB shell script
mongosh "%scriptDir%importStatement.js"
