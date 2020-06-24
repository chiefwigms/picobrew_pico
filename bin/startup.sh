#!/bin/sh
systemctl start isc-dhcp-server
wait 10
/home/pi/picobrew_pico/bin/firewall.sh
cd /home/pi/picobrew_pico
python3 zserver.py
