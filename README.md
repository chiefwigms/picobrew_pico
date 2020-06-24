# picobrew_pico
Allows for full control of the PicoBrew Pico S/C/Pro & Zymatic models.  Shout out to [@hotzenklotz](https://github.com/hotzenklotz/picobrew-server), Brian Moineau for PicoFerm API, @tmack8001 for Z series support & updates.  
[Demo Server](http://ec2-3-136-112-93.us-east-2.compute.amazonaws.com/)

## Requirements

DNS Forwarding (either through a router, RaspberryPi etc)  
  - Have a Raspberry Pi Zero W : https://albeec13.github.io/2017/09/26/raspberry-pi-zero-w-simultaneous-ap-and-managed-mode-wifi/
  - DD-WRT/Open-WRT etc : Add addional dnsmasq options `address=/picobrew.com/<Server IP running this code>`

### Option 1: Running pre packaged server via Docker
Docker v19.x (https://docs.docker.com/get-docker/)

#### Setup/Run

Setup the following directory structure for use by the server.
```
recipes/
  pico/
  zymatic/
sessions/
  brew/
    active/
    archive/
  ferm/
    active/
    archive/
```

Run server volume mounting the above directory structure

Either provide all variables to docker command directly.

```
docker run -d -it -p 80:80 \
  --mount type=bind,source=<absolute-path-to-recipes>,target=/picobrew/app/recipes \
  --mount type=bind,source=<absolute-path-to-sessions>,target=/picobrew/app/sessions \
  chiefwigms/picobrew_pico
```

To view logs check the running docker containers and tail the specific instance's logs directly via docker.

```
docker ps
CONTAINER ID        IMAGE                     COMMAND                  CREATED             STATUS              PORTS                NAMES
3cfda85cd90c        chiefwigms/picobrew_pico   "/bin/sh -c 'python3…"   45 seconds ago      Up 45 seconds       0.0.0.0:80->80/tcp   relaxed_rhodes
```

```
docker logs -f 3cfda85cd90c
WebSocket transport not available. Install eventlet or gevent and gevent-websocket for improved performance.
 * Serving Flask app "app" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:80/ (Press CTRL+C to quit)
```

### Option 2: Running server via Python directly
Python >= 3.6.9  

### Option 2: Running server on a Raspberry Pi 3
1. Use Rufus (https://rufus.ie/ I use the portable version) and "burn" buster to sdcard. 
https://www.raspberrypi.org/downloads/raspbian/ - (2020-02-13 for the guide).

2. Go ahead and create an SSH file in the root.  This will activate the SSH server and save you from going downstairs.  I speak from experience.

For Windows users: navigate to D: | Create a Next Text Document | Change the Name to SSH  (no extension)

Eject the drive safely.

3. Start up your Raspberry PI 3. Default username/pass is pi/raspberry.  Change the default password:
<pre> passwd </pre>

5. Run the following:
<pre>sudo apt-get update

6. Clone the repo in the home directory:
<pre> git clone https://github.com/chiefwigms/picobrew_pico </pre>

7. Run the setup script.
<pre> cd ~/picobrew_pico/bin
sudo ./setupRPI3.sh </pre>

<i> This script does many things. There will be some error messages. Ignore the messages about isc-dhcp-server failing to start.
a. It sets up a subnet of 192.168.42.0.  Parameters are at the top of the file.  Adjust as needed.
b. It also makes your RPI3 an acess point on the wlan0 interface.
The SSID = picobrewers. The wifi passphrase = 12345678. You may adjust both of these in the setupRPI.sh file before running or just leave them alone. 
You can change the passphrase later by editing /etc/hostapd/hostapd.conf file.
c. It installs many needed packages.
d. It creates self signed certificates. </i>

8. Reboot your RPI3
sudo reboot

9. Start the server
cd /home/pi/picobrewr_pico
sudo bin/startup.sh

10. Connect to the recipe crafter.
a. On your RPI3: navigate to localhost:8080 in the browser.
b. On another computer or phone: join the picobrewers wireless lan, then navigate to https://picobrew.com in your browser.

11. Connect your Picobrew 
a. Turn on your Zseries
b. Update the Wifi settings. Connect to SSID:picobrewers with passphrase: 12345678
c. brew



#### Setup/Run
Clone this repo, then run  
`sudo pip3 install -r requirements.txt` on *nix or `pip3 install -r requirements.txt` as an Administrator in windows  
`sudo python3 server.py` on *nix or `python3 server.py` as an Administrator in windows

## Manual Recipe Editing
The table for adding/removing/editing recipe steps has several validation checks in it, but there is always the possiblity of ruining your Pico.  
  
For Pico S/C/Pro Only: DO NOT EDIT or MOVE Rows 1-3 (Preparing to Brew/Heating/Dough In).  Drain times should all be 0 except for Mash Out (2 minutes) and the last hop addition (5 minutes) (for example, if you only have Hops 1 & 2, set the drain time on Hops 2 to 5, and remove the Hops 3 and 4 rows)

## Features
Supported Devices:
* Pico S/C/Pro: fully featured
* Zymatic: fully featured
* ZSeries (Beta)
  * Working (not tested)
    * boot up sequence
    * firmware updating / sideloading
    * recipe summary
    * session create
    * session reporting
    * close session
    * resumable session
* PicoFerm (Beta - Currently terminates fermentation after 14 days)

Device Aliasing  
Brew Sessions
* Live Graphing
* Historical Graphing

Recipe Library
* View Previously Created
* Create New Recipes

## Disclaimer
Except as represented in this agreement, all work product by Developer is provided ​“AS IS”. Other than as provided in this agreement, Developer makes no other warranties, express or implied, and hereby disclaims all implied warranties, including any warranty of merchantability and warranty of fitness for a particular purpose.
