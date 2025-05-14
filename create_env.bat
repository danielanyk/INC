@echo off
echo Checking if virtual environment folder exists...


IF EXIST env (
    echo Virtual environment already exists. Exiting script...
    exit /B
)


echo Creating and activating virtual environment...

python -m venv env
call env\Scripts\activate

echo Installing compatible PyTorch and CUDA...
@REM pip install torch==1.13.0 -f https://download.pytorch.org/whl/cu117/torch-1.13.0%2Bcu117-cp39-cp39-win_amd64.whl
@REM pip install torchvision==0.14 -f https://download.pytorch.org/whl/cu117/torch_stable.html
@REM pip install torchaudio==0.13.0 -f https://download.pytorch.org/whl/cu117/torch_stable.html

@REM pip install torch==2.0.0 -f https://download.pytorch.org/whl/cu117/torch-1.13.0%2Bcu117-cp39-cp39-win_amd64.whl
@REM pip install torchvision==0.15.0  -f https://download.pytorch.org/whl/cu117/torch_stable.html
@REM pip install torchaudio==2.0.0 -f https://download.pytorch.org/whl/cu117/torch_stable.html

pip install torch==2.0.0 torchvision==0.15.1 torchaudio==2.0.1 --index-url https://download.pytorch.org/whl/cu117


echo Installing compatible mmcv...
pip install -U openmim
mim install mmcv==2.1.0 -f https://download.openmmlab.com/mmcv/dist/cu117/torch2.0/index.html


echo Verifying installations...
python -c "import torch; print(torch.__version__)"
python -c "import mmcv; print(mmcv.__version__)"

echo Installing the rest of the packages...
pip install -r requirements.txt

python -c "import numpy; print(numpy.__version__)"

ECHO Additional Pip installs that can't be included in requirements.txt
pip install tensorflow
pip install langchain==0.0.335
pip install gradio==3.50.2
pip install llama-cpp-python==0.2.18
pip install pypdf==3.17.1
pip install reportlab
pip install jinja2
pip install ultralytics
mim install mmdet
pip install ensemble_boxes
pip install dropbox

pip install Flask-JWT-Extended

echo Setup complete.
pause
