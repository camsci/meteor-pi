# mod_settings.py
# Meteor Pi, Cambridge Science Centre
# Dominic Ford

import os

import installation_info


# The settings below control how the camera controller works

def my_installation_id():
    return installation_info.CAMERA_NAME


# The path to python scripts in the cameraControl directory
PYTHON_PATH = os.path.split(os.path.abspath(__file__))[0]

# The path to compiled binary executables in the videoProcess directory
BINARY_PATH = os.path.join(PYTHON_PATH, "../videoProcess/bin")
STACKER_PATH = os.path.join(PYTHON_PATH, "../gnomonicStack/bin")
assert os.path.exists(BINARY_PATH), "You need to compile the videoProcess C code before using this script"
assert os.path.exists(STACKER_PATH), "You need to compile the gnomonicStack C code before using this script"

# Flag telling us whether we're a raspberry pi or a desktop PC
I_AM_A_RPI = os.uname()[4].startswith("arm")

# The directory where we expect to find images and video files
DATA_PATH = os.path.join(PYTHON_PATH, "../../datadir")
assert os.path.exists(
    DATA_PATH), "You need to create a symlink 'datadir' in the root of your meteor-pi working copy, where we store all of the camera data"

# The directory where meteorpi_db stores its files
DBFILESTORE = os.path.join(DATA_PATH, "firebird_files")

# The location of the firebird database
DBPATH = "localhost:/var/lib/firebird/2.5/data/meteorpi.db"

# Flag telling us whether to hunt for meteors in real time, or record H264 video for subsequent analysis
REAL_TIME = True

# How many second before/after sun is above horizon do we wait before bothering observing
sunMargin = 1200  # 20 minutes

# When observing with non-real-time triggering, this is how many seconds in each video
VIDEO_MAXRECTIME = 7200

# Position to assume when we don't have any GPS data available
LONGITUDE_DEFAULT = installation_info.LONGITUDE
LATITUDE_DEFAULT = installation_info.LATITUDE

# Video settings. THESE SHOULD BE READ FROM THE DATABASE!
CAMERA_ID = my_installation_id()
VIDEO_DEV = "/dev/video0"
