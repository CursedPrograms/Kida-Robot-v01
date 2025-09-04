[![Twitter: @NorowaretaGemu](https://img.shields.io/badge/X-@NorowaretaGemu-blue.svg?style=flat)](https://x.com/NorowaretaGemu)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<br>
<div align="center">
  <a href="https://ko-fi.com/cursedentertainment">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="ko-fi" style="width: 20%;"/>
  </a>
</div>
<br>
<div align="center">
  <img alt="Batch" src="https://img.shields.io/badge/rasberrypi-%23323330.svg?&style=for-the-badge&logo=windows&logoColor=white"/>
</div>
<div align="center">
  <img alt="Python" src="https://img.shields.io/badge/python%20-%23323330.svg?&style=for-the-badge&logo=python&logoColor=white"/>
</div>
<div align="center">
    <img alt="Git" src="https://img.shields.io/badge/git%20-%23323330.svg?&style=for-the-badge&logo=git&logoColor=white"/>
  <img alt="PowerShell" src="https://img.shields.io/badge/PowerShell-%23323330.svg?&style=for-the-badge&logo=powershell&logoColor=white"/>
  <img alt="Shell" src="https://img.shields.io/badge/Shell-%23323330.svg?&style=for-the-badge&logo=gnu-bash&logoColor=white"/>
  <img alt="Batch" src="https://img.shields.io/badge/Batch-%23323330.svg?&style=for-the-badge&logo=windows&logoColor=white"/>
</div>
<br>

# KIDA: Kinetic Interactive Drive Automaton

dtparam=rtc_bbat_vchg=3000000
sudo mount -o remount,rw /boot/firmware
sudo nano /boot/firmware/config.txt
sudo hwclock -w
sudo hwclock -v -r

cd /home/kida-01/Desktop/Kida-Robot
source venv/bin/activate
python scripts/main.py
sudo apt install pulseaudio jackd2 alsa-utils

1. Copy Splash Screen and Set Permissions
sudo cp /home/kida-01/Downloads/splash.png /usr/share/plymouth/themes/pix/splash.png
sudo chmod 644 /usr/share/plymouth/themes/pix/splash.png
sudo chown root:root /usr/share/plymouth/themes/pix/splash.png

2. Update System and Install Hailo All-in-One Package (If available)
sudo apt update
sudo apt install hailo-all

3. Verify Hailo Runtime Installation
hailortcli fw-control identify

Expected output:
Device: Hailo-8
PCIe Address: 0001:03:00.0
Firmware Version: x.x.x

4. Python Connectivity Test Script (Optional)
import subprocess

def check_hailo():
    try:
        result = subprocess.check_output(["hailortcli", "fw-control", "identify"]).decode()
        print("✅ Hailo connected:\n", result)
    except Exception as e:
        print("❌ Hailo not detected:", e)

check_hailo()

5. If HailoRT is NOT installed, Manual Build Instructions:
sudo apt update
sudo apt install -y git build-essential cmake python3-dev python3-pip
git clone https://github.com/hailo-ai/hailort.git
cd hailort
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install

git clone https://github.com/protocolbuffers/protobuf.git
cd protobuf
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install

echo "export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH" >> ~/.bashrc
source ~/.bashrc
pip install hailort
hailortcli fw-control identify

# 1. Make sure you have venv and pip installed
sudo apt update
sudo apt install python3-venv python3-pip

# 2. Create a virtual environment
python3 -m venv ~/kida-venv

# 3. Activate the environment
source ~/kida-venv/bin/activate

# 4. Install whisper inside the venv
pip install --upgrade pip
pip install git+https://github.com/openai/whisper.git

cd /home/kida-01/Desktop/Kida-Robot && python3 main.py &
sudo crontab -e
@reboot cd /home/kida-01/Desktop/Kida-Robot && python3 main.py &
ctrl+x ctrl+s

source ~/kida-venv/bin/activate
python3 /home/kida-01/Desktop/Kida-Robot/main.py
python3 /home/kida-01/Desktop/Kida-Robot/pi-chat.py

sudo nano /etc/systemd/system/kida-camera.service

[Unit]
Description=KIDA Camera Live Preview
After=graphical.target

[Service]
User=kida-01
Environment=DISPLAY=:0
ExecStart=/usr/bin/python3 /home/kida-01/Desktop/Kida-Robot/scripts/camera_preview.py
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target

sudo systemctl daemon-reload
sudo systemctl enable kida-camera.service
sudo systemctl start kida-camera.service

sudo systemctl status kida-camera.service
journalctl -u kida-camera.service -f

sudo fuser -v /dev/video0

ps -ef | grep -i camera

sudo -u kida-01 DISPLAY=:0 /usr/bin/python3 /home/kida-01/Desktop/Kida-Robot/scripts/camera_preview.py

ps aux | grep -E 'libcamera|picamera'
sudo kill -9 <PID>

sudo apt install -y portaudio19-dev python3-pyaudio

libcamera-hello

sudo -u kida-01 DISPLAY=:0 /usr/bin/python3 /home/kida-01/Desktop/Kida-Robot/scripts/camera_preview.py

## Rasberry Pi 5 Robot

pip install git+https://github.com/elevenlabs/elevenlabs-python@v3

### OS:
Rasberry OS [Recommended!] (you can use any distro you choose)

### Parts:

- Robot Tank Chassis (XiaoR Geek [Recommended!])
- L298N Motor Driver
- Rasberry Pi 5
- Pi 5 Speaker  Hat
- Pi NVME + AI Hat
- NVME
- HAILO 8 (13 TOPS)
- 1x Pi 5 Nightvision Camera (Slot 0)
- 1x Pi 5 AI Camera Camera (Slot 1)
- 2x Pi Camera Holder
- 2x Ardiuno
- 1x Motion Detector
- 2x Ultrasonic Sensor
- 1 VL53L0X T-o-F Sensor
- 1x Metal Detector
- 1x UV Sensor
- 1x 3 channel line tracker
- 1 ball tiltswitch
- 1/2x LED Strip
- 2x MOSFET Switches (+ 12v LEDs)
- I2C Devices: 
-- 3x 16850 Pi UPS*

- Servo Motor
- 2 x Power Switches
- 2x 12v DCMotor
- DuPont Cables
- 3s 21700 Batteryholder - Connected to buck converter set to 11.5v
- 3x 21700 Batteries
- 3x 16850 Batteries
- 1 USB Microphone

### Electonic Schematic:

#### Motor A (Left)
L298N Pin	Function	Pi GPIO
IN1	Direction	GPIO 17
IN2	Direction	GPIO 27
ENA	Speed (PWM)	GPIO 18 (hardware PWM capable)*

#### Motor B (Right)
L298N Pin	Function	Pi GPIO
IN3	Direction	GPIO 22
IN4	Direction	GPIO 23

(11.1V)

[12V Battery Pack 3S 21700 Battery 3.7v]
 ├── + ─────────► L298N VS       (motor power input)
 ├── + ─────────► LM2596S IN+    (step-down input for Pi)
 ├── – ─────────► L298N GND
 └── – ─────────► LM2596S IN–

[LM2596S Output]
 ├── OUT+ ──────► Pi 5V (GPIO pin 2 [[Not Recommended!] Pi UPS via USB-C cable [Recommended!]])
 └── OUT– ──────► Pi GND (GPIO pin 6 or 9)

## How to Run:

### Install Requirements

Using Python directly:
pip install -r requirements.txt

Or run: 
- install_requirements.bat

<br>

~/.config/autostart

nano ~/.config/autostart/kida.desktop

[Desktop Entry]
Name=KIDA Controller
Exec=python3 /home/pi/path/to/main.py
Type=Application
X-GNOME-Autostart-enabled=true

### FFMpeg Setup (Windows)

1. Download FFMpeg  
   Visit the following link and download the latest static build:  
   https://www.gyan.dev/ffmpeg/builds/

2. Extract the Archive  
   Unzip the downloaded archive to C:\.

3. Rename and Organize  
   Rename the extracted folder to ffmpeg, and ensure the following folder structure:

C:\ffmpeg\bin
├── ffmpeg.exe
├── ffplay.exe
└── ffprobe.exe

4. Set Environment Variable (Optional for Global Access)  
   To make ffmpeg accessible system-wide:

   - Open System Properties > Environment Variables
   - Under User variables (for your PC username), find and select Path
   - Click Edit > New and paste:
     C:\ffmpeg\bin
   - Click OK to apply the changes
  
5. Test it
     Close and reopen your terminal (CMD), then type:
    ffmpeg -version
    If it prints the version info, you're good.

CRONTAB:

crontab -e

@reboot python3 /home/pi/path/to/main.py

sudo raspi-config

### Run main.py

Using Python directly:
python main.py

Using provided scripts:

Windows:
- .\run.bat
or
- .\run.ps1

Unix-like systems (Linux/macOS):
- .\run.sh

<br>

## Requirements:

playsound
openai-whisper
sounddevice==0.5.1
numpy
SpeechRecognition
pygame
requests
elevenlabs==0.2.26
torch==2.6.0
torchaudio
gTTS
soundfile
sseclient
RPi.GPIO
flask
psutil
opencv-python
picamera2
smbus2
jinja2
Werkzeug
itsdangerous
click
pyserial
ultralytics
loguru
scipy==1.9.3
lap
cython_bbox
transformers==4.50.1
tqdm
deepface
pillow
sounddevice==0.5.1
tqdm
tf-keras
faster-whisper



<br>
<div align="center">
© Cursed Entertainment 2025
</div>
<br>
<div align="center">
<a href="https://cursed-entertainment.itch.io/" target="_blank">
    <img src="https://github.com/CursedPrograms/cursedentertainment/raw/main/images/logos/logo-wide-grey.png"
        alt="CursedEntertainment Logo" style="width:250px;">
</a>
</div>
<br>
<div align="center">
<a href="https://github.com/SynthWomb" target="_blank" align="center">
    <img src="https://github.com/SynthWomb/synth.womb/blob/main/logos/synthwomb07.png"
        alt="SynthWomb" style="width:200px;"/>
</a>
</div>
