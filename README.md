# callhome project

Device based on Raspberry Pi used for face tracking and camera pan-tilt during messenger call.

Good performance was achieved with Raspberry Pi 4B 8GB.

Requires installation of Python3 and PyQt5 on Raspberry Pi. See install-pyqt5 folder.
https://www.inemov.com/post/install-and-troubleshoot-pyqt5-on-raspberry-pi

I used  Waveshare 7" touch screen that required certain actions to set-up right touch to call context menu. See set-up-right-click folder.
https://www.inemov.com/post/set-rightclick-rpi-waveshare7-touchscreen

Once all is installed, put all .py .xml .csv files from repository root to Raspberry PI folder and set up script execution on start-up (see RPi-autostart folder).
