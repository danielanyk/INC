@echo off
REM Changing Work Directory 
echo Current Working Directory: %cd%
call .\env\Scripts\Activate.bat
python .\apps\home\Engines\engine_summarization.py
