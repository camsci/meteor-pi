# module_settings.py
# Meteor Pi, Cambridge Science Centre
# Dominic Ford

import os

# The settings below control how the camera controller works

# The path to python scripts in the cameraControl directory
PYTHON_PATH = os.path.split( os.path.abspath(__file__) )[0]

# The path to compiled binary executables in the videoProcess directory
BINARY_PATH = os.path.join(PYTHON_PATH , "../videoProcess/bin")

# Flag telling us whether we're a raspberry pi or a desktop PC
I_AM_A_RPI  = os.uname()[4].startswith("arm")

# The directory where we expect to find images and video files
DATA_PATH   = "../../datadir"
assert os.path.exists(DATA_PATH), "You need to create a symlink 'datadir' in the root of your meteor-pi working copy, where we store all of the camera data"

# Flag telling us whether to hunt for meteors in real time, or record H264 video for subsequent analysis
REAL_TIME   = False

# How many second before/after sun is above horizon do we wait before bothering observing
sunMargin   = 1200 # 20 minutes

