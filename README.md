# picobrew_pico
[![Python Application](https://github.com/tmack8001/picobrew_pico/actions/workflows/python-app.yml/badge.svg?event=push)](https://github.com/tmack8001/picobrew_pico/actions/workflows/python-app.yml)

[![GitHub Release][releases-shield]][releases]
![GitHub all releases][download-all]
![GitHub release (latest by SemVer)][download-latest]
[![GitHub Activity][commits-shield]][commits]


Allows for full control of the PicoBrew Pico S/C/Pro & Zymatic models.  Shout out to [@hotzenklotz](https://github.com/hotzenklotz/picobrew-server), Brian Moineau for PicoFerm API, @tmack8001 for Z series support & updates.  
[Demo Server](http://ec2-3-136-112-93.us-east-2.compute.amazonaws.com/)

## Supported Devices:
* Hot Side
  * Pico S/C/Pro: fully featured
  * Zymatic: fully featured
  * ZSeries: fully featured
  * PicoStill: fully featured
    * Optional internal PicoStill T1/2/3/4 and Pressure Logging 
    * Firmware versions 0.0.30 - 0.0.35 (selectable)
    * PicoBrew Controlling Devices:
      * Pico S/C/Pro distillation (no heat sensor logging - limitation of firmware)
      * ZSeries (full heat sensor logging - included and supported within Z firmware)
      * Zymatic (no native support for controlling the PicoStill - limitation of firmware)
* Cold Side (Fermentation)
  * PicoFerm (Beta - Currently terminates fermentation after 14 days)
  * iSpindel: full session graphing
  * Tilt: full session graphing

## Features
* Device Aliasing
* Brew Sessions
  * Live Graphing
  * Historical Graphing
* Recipe Library
  * View Previously Created
  * Create New Recipes
  * Import from PicoBrew Servers (Pico C/S/Pro and Zymatic)
* Manual Recipe Editing
  * **Note** The table for adding/removing/editing recipe steps has several validation checks in it, but there is always the possibility of ruining your Pico.  
  * *For Pico S/C/Pro Only*: DO NOT EDIT or MOVE Rows 1-3 (Preparing to Brew/Heating/Dough In).  Drain times should all be 0 except for Mash Out (2 minutes) and the last hop addition (5 minutes) (for example, if you only have Hops 1 & 2, set the drain time on Hops 2 to 5, and remove the Hops 3 and 4 rows)

## Installation
[![GitHub Release][releases-shield]][releases]
![GitHub all releases][download-all]
![GitHub release (latest by SemVer)][download-latest]

Refer to the [Releases Page](https://github.com/chiefwigms/picobrew_pico/releases) for steps to get up and running with your own Pico server with a Raspberry Pi device (recommended models include: Raspberry Pi Zero-W or Raspberry Pi 4).

By default the hostname of the RaspberryPi device will be "raspberrypi" and is discoverable on your local network along with the "samba" (or network shares) for sessions and recipes. You can use these to view the files created by the server during interactions with the user and connected devices.

### Debugging Issues

There are two primary ways to help get additional details of errors that occur.

First is to see what is happening in your local browser. Most modern browsers have "development tools" that are included (in Chrome "Settings > More Tools > Developer Tools") and from these there are usually a console log as well as a "Network" tab that shows all the network requests made by the existing experience/page.

Second is to view the application logs from the included python server over an ssh or local keyboard+screen session.

```
sudo systemctl status rc.local -n <num-log-lines>
```

The remainder of this guide is oriented around creating a development environment for contributors.

# Development Setup

## Requirements

DNS Forwarding (either through a router, RaspberryPi etc)  
  - Have a Raspberry Pi Zero W : https://albeec13.github.io/2017/09/26/raspberry-pi-zero-w-simultaneous-ap-and-managed-mode-wifi/
  - DD-WRT/Open-WRT etc : Add additional option added to dnsmasq.conf: `address=/picobrew.com/<Server IP running this code>`

### Option 1: Running pre packaged server via Docker or Docker-Compose
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

Run server volume mounting the above directory structure.

##### (Optional) Step 1: Generate SSL Certs

If you are looking to support a ZSeries device which requires HTTP+SSL communication we need to generate some self-signed certificates to place in front of the flask app. These will be used when running nginx to terminate SSL connection before sending the requests for processing by flask.

```
./scripts/docker/nginx/ssl_certificates.sh
```

On MacOS you can add permanent trust for the Certificate Authority (yourself) if you use Chrome and/or Safari this makes it so that the authority of the certificate generated above is trusted. Only these browsers check keychain access to get a list of CAs whereas Firefox stores its own list of trusted CAs in the browser.

```
sudo security add-trusted-cert -d -r trustAsRoot -k /Library/Keychains/System.keychain $(pwd)/scripts/docker/nginx/certs/bundle.crt
```

##### Step 2: Run Flask Server (optionally with `docker run` or with `docker-compose`)

Either provide all variables to docker command directly or use the repository's docker-compose.yml (which will also include a working SSL enabled nginx configuration given you have setup certificates correctly with `./scripts/docker/nginx/ssl_certificates.sh`)

###### Option 1: Docker Run (without SSL support or external SSL termination)

Running straight with docker is useful for easy setups which don't require SSL connections (aka non ZSeries brew setups) and/or for those that leveraging another existing system to handle the SSL connections (ie. mitmproxy, nginx, etc).

```
docker run -d -it -p 80:80 --name picobrew_pico \
  --mount type=bind,source=<absolute-path-to-recipes>,target=/picobrew_pico/app/recipes \
  --mount type=bind,source=<absolute-path-to-sessions>,target=/picobrew_pico/app/sessions \
  chiefwigms/picobrew_pico
```

To view logs check the running docker containers and tail the specific instance's logs directly via docker.

```
docker ps
CONTAINER ID        IMAGE                     COMMAND                  CREATED             STATUS              PORTS                NAMES
3cfda85cd90c        chiefwigms/picobrew_pico   "/bin/sh -c 'python3…"   45 seconds ago      Up 45 seconds       0.0.0.0:80->80/tcp   picobrew_pico
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

###### Option 2: Docker Compose (with SSL support via a dedicated nginx container)

To run a setup with http and https and want to have the ssl termination handled by the included nginx `docker-compose` is the easiest configuration to go with.

```
docker-compose up --build
```

or to start the servers in the background

```
docker-compose up --build -d
```

To view logs use the aliases service name `app` to view logs via the docker-compose command.

```
docker-compose logs -f app
```

### Option 2: Running server via Python directly (optionally terminating ssl elsewhere manually)
Python >= 3.6.9  

#### Setup/Run
Clone this repo, then run  
`sudo pip3 install -r requirements.txt` on *nix or `pip3 install -r requirements.txt` as an Administrator in windows  
`sudo python3 server.py` on *nix or `python3 server.py` as an Administrator in windows (default host interface is `0.0.0.0` and port `80`, but these can be specified via command-line arguments like so `python3 server.py <interface> <port>`)

## Disclaimer
Except as represented in this agreement, all work product by Developer is provided ​“AS IS”. Other than as provided in this agreement, Developer makes no other warranties, express or implied, and hereby disclaims all implied warranties, including any warranty of merchantability and warranty of fitness for a particular purpose.
