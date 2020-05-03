# picobrew_pico
Allows for full control of the PicoBrew Pico S/C/Pro models.  Shout out to https://github.com/hotzenklotz/picobrew-server

## Requirements
Python >= 3.6.9  
DNS Forwarding (either through a router, RaspberryPi etc)  
  - Have a Raspberry Pi Zero W : https://albeec13.github.io/2017/09/26/raspberry-pi-zero-w-simultaneous-ap-and-managed-mode-wifi/
  - DD-WRT/Open-WRT etc : Add addional dnsmasq options `address=/picobrew.com/<Server IP running this code>`

## Setup/Run
Clone this repo, then run  
`pip install -r requirements.txt`  
`sudo python3 server.py` on *nix or `python3 server.py` as an Administrator in windows

## Manual Recipe Editing
The table for adding/removing/editing recipe steps has several validation checks in it, but there is always the possiblity of ruining your Pico.  DO NOT EDIT or MOVE Rows 1-3 (Preparing to Brew/Heating/Dough In).  Drain times should all be 0 except for Mash Out (2 minutes) and 5 minutes for the last hop addition (for example, if you only have Hops 1 & 2, set the drain time on Hops 2 to 2, and remove the Hops 3 and 4 rows)

## Features
Live session graphing  
Historical session graphing  
Recipe Library  
Recipe Additions  

## Disclaimer
Except as represented in this agreement, all work product by Developer is provided ​“AS IS”. Other than as provided in this agreement, Developer makes no other warranties, express or implied, and hereby disclaims all implied warranties, including any warranty of merchantability and warranty of fitness for a particular purpose.
