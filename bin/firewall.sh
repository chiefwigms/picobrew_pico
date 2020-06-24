#!/bin/sh

iptables -F
iptables-restore < /home/pi/picobrew_pico/bin/firewall.rules
