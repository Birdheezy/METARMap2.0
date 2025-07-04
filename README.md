# NOTE: 
### The "main" branch is my "beta" branch. It's where I commit my nightly work and can be unstable. Please use the "production" branch for your own projects. 
 
This is a complete rewrite of my METARMap Project. It was inspired by others who have created a similar project. I wanted it to be easy enough to set up so that a complete beginner could do it!

# Main features of this project

## Simplicity
I wanted this to be so easy, a complete beginner could set it up. See my YouTube video here: https://youtu.be/eBfOBHSns-k?si=zkOn1fk1ZZcP1HTu

## Ease of use
Once the map is set up it should be easy to play with! Part of the fun of this project is building on it and adding more features. The novice user should be able to click the "update" button in the settings website and get all the new features "just like that".

## FUN!
It should be fun to change the settings, update the weather and see what is happening in your area!

## Community involvement
I hope people find this project and collaborate on it. I'm not here to make money as this is a passion project. Please submit bug reports and feature requests! If you notice anything wonky in the code, let me know! 

## Sunrise/Sunset Automation
The system can automatically calculate and adjust LED brightness based on actual sunrise and sunset times for your location. Simply select your city from a dropdown list, and the system will:
- Calculate sunrise and sunset times daily
- Automatically adjust LED brightness at sunrise (bright) and sunset (dim)
- Handle seasonal changes automatically
- Support major US cities across all time zones

# Software Install instructions
## Setup.sh

There is now a batch script that will guide you through the setup. After first boot of the pi, SSH into the Pi and run this command `curl -sSL https://raw.githubusercontent.com/Birdheezy/METARMap2.0/production/setup.sh -o setup.sh && chmod +x setup.sh && sudo ./setup.sh`. It will download the setup.sh file and run it. 

Alternatively you can copy over setup.sh to /home/pi and run "sudo bash setup.sh" the script will walk you through everything. 

If you get an error when running setup.sh, run `sed -i 's/\r$//' setup.sh`. This will fix the line endings then re-run `sudo bash setup.sh`

Or

After writing the OS to the SD card, a window should pop up. If you copy setup.sh to that folder, you can then connect via SSH and run `sudo mv /boot/firmware/setup.sh /home/pi/`. 
This will move setup.sh to the home/pi folder, where you can then run `sudo bash setup.sh`
If you get an error run `sed -i 's/\r$//' setup.sh`

## Pi Setup
I suggest using a Pi zero 2 w. It's cheap enough and more than powerful enough for this project. a pi zero w will work it's just a little slower.

1. Download the Pi imiger https://www.raspberrypi.com/software/
2. I use a 16gb micro sd card but 8 will work as well. 
3. Choose whichever device you're using (i.e. pi zero 2 w)
4. Choose your OS. Go to Raspberry Pi OS (other) then Raspberry Pi OS Lite (32-bit)
5. Choose your storage (your SD card)
6. Click Next then "edit settings". Set the HOSTNAME and username to "pi" and configure you WiFi setup. Also enter a password that you'll use to log into your pi.
7. Go to the "services" tab and Check the box for "enable SSH" and choose "Use Password Authentication"
8. Go to the Options tab. Choose "Eject media when finished"

Allow the the card to be written and varified. It can take 5-10 min for this process. While this is happeneing you can download putty (https://www.putty.org/) and install it.
When the SD card is finished you can remove it and put it into your Pi. Plug your Pi into a power source and let it boot. It can take 5-10 min for the frist boot and for the pi to show up on your wifi. 

## Connecting to your Pi


There are several ways to find your Pi's IP address and connect to it:

### Finding your Pi's IP address

1. **Router method**: Go to your WiFi router's settings page and find the Pi in the connected devices list. Look for a device named "pi" or whatever hostname you set during setup.

2. **Hostname method**: Most modern networks support mDNS (Bonjour), which allows you to connect using the hostname:
   - If you set the hostname to "pi" during setup, you can use `pi.local` to connect
   - On Windows, open Command Prompt or Powershell and type `ssh pi@pi.local` (continue below)
   - On Mac/Linux, open Terminal and type `ssh pi@pi.local` (continue below)

### Connecting via SSH

#### Using Putty (Windows)
1. Download and install [Putty](https://www.putty.org/)
2. Open Putty and in the "Host Name (or IP address)" field, enter:
   - `pi@XXX.XXX.X.XXX` (replace with your Pi's IP address), or
   - `pi@pi.local` (if using hostname)
3. Keep Port as 22 and Connection type as SSH
4. Click "Open" and accept the security alert if it appears
5. Enter your password when prompted (note: characters won't display as you type)

#### Using Terminal (Mac/Linux)
1. Open Terminal
2. Type: `ssh pi@XXX.XXX.X.XXX` (replace with your Pi's IP address) or `ssh pi@pi.local`
3. Type `yes` if asked to confirm the connection
4. Enter your password when prompted

#### Using PowerShell (Windows)
1. Open PowerShell
2. Type: `ssh pi@XXX.XXX.X.XXX` (replace with your Pi's IP address) or `ssh pi@pi.local`
3. Type `yes` if asked to confirm the connection
4. Enter your password when prompted. NOTE nothing will appear as you type your password

You should now see a command prompt like `pi@pi:~ $` which indicates you're successfully connected to your Pi.

1. Go to your WiFi routers settings and find the pi and it's local IP address.
2. Open putty and in the Hostname (or IP) box, enter pi@XXX.XXX.X.XXX <-- the local IP address of your Pi that you got from your router. The port should be 22 and "connection type" is SSH.
3. Click "open". You should get a pop up asking if you trust this device. Click Yes. You should then have a black terminal window asking for a password. Enter the password you set up earlier. NOTE: nothing will show up as your type your password. Hit enter.
4. You sould now see pi@pi:~ $


## Installing Packages
NOTE: When i say "run ```sudo apt update```" that means type the command "sudo apt update" (without the quotes) into the terminal window and hit enter. Some of these commands can take anywhere from a second to a few minutes to run. Be patient! Also, using ctrl+v to past into putty dones't work, simply copy the code snipit from here, then right click in putty. This should past the command. 

1. run ```sudo apt update``` <-- This updates the list of packages the pi can see
2. run ```sudo apt upgrade -y``` <-- this now updates any packages on the pi that need it. This can take some time.
3. We now need to create a virtual environment for some of our libraries to run inside. This is updated to work with the newest version of Pi OS - Bookworm.
4. run `python3 -m venv --system-site-packages metar` "metar" can be changed to whatever you want to call your VE. However, keep in mind that any of the aliases we set up later will have to be changed to match wahtever you call for virtual environment.
5. We need to activate the VE. Run ```source metar/bin/activate``` You should now see "(metar) pi@pi:~ $". Any packages/libraries we install here will now be separated from the rest of the OS.
6. We need to install the neopixel library, flask, requests and schedule libraries. Run each of the following commands. Remember to be patient as each installs. If they ask you in you want to install it, type "y" or "yes" as directed and hit enter.
7. ```pip3 install adafruit-circuitpython-neopixel``` <-- Neopixel library that controlls the LEDs
8. ```pip3 install flask``` <-- flask is what runs the settings website
9. ```pip3 install requests``` <-- required for the code to make requests
10. ```pip3 install schedule``` <-- required for the lights to schedule an on and off time
11. We can now deactivate the VE. Run `deactivate`

## WiFi broadcasting

This is optional but helpful. If your pi ever drops off yoru WiFi network, it will broadcast its own wifi network that you can connect to so you can then add it back to your wifi. This runs in the background and is lightweight. When the Pi boots, it looks for any known networks. If it doesn't find one, it broadcasts its own. Or if you change your wifi password and the Pi is unable to connect, it will then broadcast its own network again.
The project can be found here but the instructions are below: https://www.raspberryconnect.com/projects/65-raspberrypi-hotspot-accesspoints/203-automated-switching-accesspoint-wifi-network

1. Run the following commands:
2. ```curl "https://www.raspberryconnect.com/images/scripts/AccessPopup.tar.gz" -o AccessPopup.tar.gz``` <-- Downloads the compressed file we need. 
3. ```tar -xvf ./AccessPopup.tar.gz``` <-- uncompresses the file
4. ```cd AccessPopup``` <-- moves into the directory we just uncompressed
5. ```sudo ./installconfig.sh``` <-- runs the install script for the software.
6. Choose option 1 to install. (type "1" then enter)
7. After installing, you can customize the IP address, wifi network name and password if you wish. You can also force the Pi to drop off your wifi network and broadcast it's own network from this menu as well.
8. After you exit the installer, go back to the home directory with ```cd ~``` and hit enter. You should see "pi@pi:~ $"

## Install Git
Again, this is optional but will be mandatory to have if you want to use the "check for updates" button in the settings website. It's also the easiest way to get the files onto the pi that run the metar program. 

1. You should be in the home/pi directory (pi@pi:~ $)
2. ```sudo apt install git``` <-- installs git
3. ```git init``` <-- initializes git in the /home/pi directory
4.  ```git remote add origin https://github.com/Birdheezy/METARMap2.0``` <-- this adds the repo
5.  ```git fetch origin``` <-- fetches files
6.  ```git checkout -t origin/production``` <-- copies the files to the home/pi directory (replace "production" with "main" for the nightly build. Not recommended)
7.  To ensure the files are now there, type ```ls``` and hit enter. you should see a whole list of files like airports.txt, blanks.py, config.py etc 

## Services
Services on the pi allow a script or program to run at an elevated level. We will create some services for different files that we have. 

`cd /etc/systemd/system/` <— change directoey

We will create 4 services. One for metar.py and one for scheduler.py one for wather.py and one for settings.py
`sudo nano settings.service`

When asked which editor you'd like to use, select nano (option 1) and hit enter. You should now be presented with a mostly blank screen. Copy over 

When asked which editor you'd like to use, select nano (option 1) and hit enter. You should now be presented with a mostly blank screen. Copy over 

```
[Unit]

Description=Run Flask App for Settings
After=network.target

[Service]

WorkingDirectory=/home/pi/
ExecStart=sudo /home/pi/metar/bin/python3 /home/pi/settings.py
Restart=on-failure
User=pi
StandardOutput=journal
StandardError=journal

[Install]

WantedBy=multi-user.target
```

ctrl+x, y, enter to save.

`sudo nano scheduler.service`

```
[Unit]
Description=Scheduler Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/pi
ExecStart=sudo /home/pi/metar/bin/python3 /home/pi/scheduler.py
Restart=always
User=pi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Ctrl+x, y, enter to save. 

`sudo nano metar.service`

```
[Unit]
Description=Run Metar Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/pi
ExecStart=/home/pi/metar/bin/python3 /home/pi/metar.py
Restart=always
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```
ctrl+x, y, enter to save

`sudo nano weather.service`

```
[Unit]

Description=Run Weather Service
After=network.target

[Service]

WorkingDirectory=/home/pi/
ExecStart=sudo /home/pi/metar/bin/python3 /home/pi/weather.py
Restart=10
User=root
StandardOutput=append:/var/log/weather.log
StandardError=append:/var/log/weather.log

[Install]

WantedBy=multi-user.target
```
ctrl+x, y, enter to save


Run 
`sudo systemctl daemon-reload`
Thus will reload the services daemon so our changes will be seen by the system.

Navigate back to the home directory
`cd ~` 

## Aliases
To make running the services and scripts easier we will add some aliases
`sudo nano ~/.bash_aliases`
Copy over the following 

```
alias blank='sudo /home/pi/metar/bin/python3 blank.py'
alias metar='sudo /home/pi/metar/bin/python3 '
alias startmetar='sudo systemctl start metar.service'
alias startweather='sudo systemctl start weather.service'
alias startscheduler='sudo systemctl start scheduler.service'
alias startsettings='sudo systemctl start settings.service'
alias stopmetar='sudo systemctl stop metar.service'
alias stopweather='sudo systemctl stop weather.service'
alias stopsettings='sudo systemctl stop settings.service'
alias stopscheduler='sudo systemctl stop scheduler.service'
alias restartmetar='sudo systemctl restart metar.service'
alias restartweather='sudo systemctl restart weather.service'
alias restartsettings='sudo systemctl restart settings.service'
alias restartscheduler='sudo systemctl restart scheduler.service'
alias metarstatus='sudo systemctl status metar.service'
alias weatherstatus='sudo systemctl status weather.service'
alias settingsstatus='sudo systemctl status settings.service'
alias schedulerstatus='sudo systemctl status scheduler.service'
```

ctrl+x, y, enter to save. 

To reload the aliases file for our changes to take affect, run
`source .bash_aliases`
Now you can simply use any alias to run its respective command. For example, instead of running 
`sudo /home/pi/metar/bin/python3 metar.py`
To run metar.py, you can run
`metar metar.py`
use ctrl+c to exit the script. 

As you can see in the list if aliases we copied over, the 2nd alias is "alias metar=…" 
The same is true for starting the metar service. Simply type `startmetar` and hit enter and the service will start in the background. 
To have the metar.py script start at boot, run 
`sudo systemctl enable metar.service`
And 
`sudo systemctl enable scheduler.service`