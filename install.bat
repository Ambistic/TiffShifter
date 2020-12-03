@ECHO OFF
ECHO setting up virtual env
python -m venv tif
ECHO installing packages
CALL .\tif\Scripts\activate
pip install PySide2 Pillow numpy==1.19.3
echo Now open `run.bat` or in command line `python main.py`
PAUSE