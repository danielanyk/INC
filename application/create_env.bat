echo Creating and activating virtual environment...

python -m venv env
call env\Scripts\activate

echo Installing compatible PyTorch and CUDA...
pip install torch==2.5.1
pip install torchvision==0.20.1

echo Verifying installations...
python -c "import torch; print(torch.__version__)"
@REM python -c "import mmcv; print(mmcv.__version__)"

echo Installing the rest of the packages...
pip install -r requirements.txt

@REM python -c "import numpy; print(numpy.__version__)"

ECHO Additional Pip installs that can't be included in requirements.txt
pip install ultralytics


echo Setup complete.
pause