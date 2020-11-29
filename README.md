# HDMI CEC to ADB

Turns off an Android TV using a Raspberry Pi and adb shell commands. Not all Android TVs respect the HDMI "standby" 
command (even if the HDMI-CEC settings are enabled) and as result, the won't turn off automatically when a 
standby broadcast message is sent via HDMI. 

This package aims to solve that using `python-cec` / `libcec` and `adb` (Android Debug Bridge). When a broadcast 
standby command has been sent, this program sends an adb shell command to turn off the TV using key input.

## Installation

There are a few steps to getting all the pieces working.

### Android TV Setup

Turn on your Android TV "Developer Mode" and enable adb debug logging.

### Install Raspbian

For this setup to work, you will need a Raspberry PI and will need to complete the guide from 
[PiMyLifeUp](https://pimylifeup.com/raspberrypi-hdmi-cec/). This basically installs a Raspberry PI with
Raspbian and `cec-client` which is required to communicate with HDMI and used by this library.

### Copy adb keys

You will need to copy public and private keys to your `/home/pi/.android/` folder on the Raspberry PI. These could be
taken from any computer were `adb` is installed. These allow from communication over TCP/IP and to turn off the TV.

### Install hdmi_cec_to_adb

Once your Raspberry PI is setup, install hdmi_cec_to_adb and setup a cron to automatically start on boot.

```bash
# assuming you have virtualenvwrapper already installed
mkvirtualenv hdmi_cec_to_adb

pip install hdmi-cec-to-adb
```

```bash
# Add the following to your crontab and make sure you use your TV IP Address
SHELL=/bin/bash
@reboot source /home/pi/.virtualenvs/hdmi_cec_to_adb/bin/activate && start_hdmi_cec_monitor --tv_ip_address=192.168.1.99 --adb_key_filepath=/home/pi/.android/adbkey
```
