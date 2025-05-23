@echo off
echo Current Working Directory: %cd%

echo Starting Engine...
echo 

::conda activate inc_env
@REM C:\Users\DanielYeoh\anaconda3\envs\inc_env\python.exe apps\engines\drain.py
call .\env\Scripts\Activate.bat
python .\apps\home\Engines\drain.py