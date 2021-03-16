# TiffShifter
Small UI application to remove shifts from video microscopy


## Installation

### Prerequisites
First, make sure to have python3 installed (for windows especially).

To test if you have python3 on windows :
- Press "Super + R" (Super is the "windows" key between Ctrl and Alt on the bottom left of the keyboard)
- Type `cmd`
- Press Enter
- Type `python`

You should something like :
```
Python 3.8.5 (default, Jul 28 2020, 12:59:40) 
[GCC 9.3.0] on windows
Type "help", "copyright", "credits" or "license" for more information.
>>> 
```

To leave, type `exit()` then `exit`

If python3 is not installed on windows, go on the Microsoft Store and install
python3.9


### For windows
Make sure you have all the prerequisite  
Download the zip file (green button "code")  
Unzip the file

To install, double click on `install.bat`

Then to run, double click on `run.bat`

If you want a Desktop shortcut, right click on `run.bat`, click on `Send To` (Envoyer vers) and `Desktop shortcut`


### For MacOS / Linux
Run in a shell

To install
```bash
# For MacOS only
xcode-select --install

git clone https://github.com/Ambistic/TiffShifter.git
cd TiffShifter
python3 -m venv tifenv
source tifenv/bin/activate
python3 -m pip install PySide2 Pillow numpy
```

To run
```bash
# be sure to be in the TiffShifter folder (use `pwd`)
source tifenv/bin/activate
python3 main.py
```

To update
```bash
# be sure to be in the TiffShifter folder (use `pwd`)
git pull origin main
```
