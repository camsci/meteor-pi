# mod_relay.py
# Meteor Pi, Cambridge Science Centre
# Dominic Ford

# -------------------------------------------------
# Copyright 2016 Cambridge Science Centre.

# This file is part of Meteor Pi.

# Meteor Pi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Meteor Pi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Meteor Pi.  If not, see <http://www.gnu.org/licenses/>.
# -------------------------------------------------

import RPi.GPIO as GPIO

import installation_info
from mod_log import log_txt


def camera_on():
    log_txt("Turning camera on.")
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(installation_info.local_conf['gpioPinRelay'], GPIO.OUT)
    GPIO.output(installation_info.local_conf['gpioPinRelay'], installation_info.local_conf['relayOnGPIOState'])


def camera_off():
    log_txt("Turning camera off.")
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(installation_info.local_conf['gpioPinRelay'], GPIO.OUT)
    GPIO.output(installation_info.local_conf['gpioPinRelay'], not installation_info.local_conf['relayOnGPIOState'])

    # Some relays need 5V, and the 3.3V generated by a Pi isn't enough to switch them off. But setting them as an input does the trick...
    GPIO.setup(installation_info.local_conf['gpioPinRelay'], GPIO.IN)

