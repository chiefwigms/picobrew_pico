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
  --mount type=bind,source=<absolute-path-to-recipes>,target=/app/recipes \
  --mount type=bind,source=<absolute-path-to-sessions>,target=/app/sessions \
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
