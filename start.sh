pkill solarwhisper
cd /home/pi/SolarKicker
make program
cd /home/pi/SolarWhisper
nohup python main.py > /dev/null 2>&1&
