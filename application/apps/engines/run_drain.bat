@echo off
echo Current Working Directory: %cd%

echo Starting Engine...
echo 

::conda activate inc_env
@REM C:\Users\DanielYeoh\anaconda3\envs\inc_env\python.exe apps\engines\drain.py
call application\env\Scripts\activate
python application\apps\engines\drain.py