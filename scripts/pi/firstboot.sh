#!/bin/bash
# Run as sudo/root
exec &> /firstboot.log

function killService() {
  service=$1
  systemctl stop $service
  systemctl kill --kill-who=all $service
  while ! (systemctl status "$service" | grep -q "Main.*code=\(exited\|killed\)")
  do
    sleep 2
  done
}

# AP for Pico devices
# SSID Must be > 8 Chars
AP_IP="192.168.72.1"
AP_SSID="PICOBREW"
AP_PASS="PICOBREW"

# Enable root login
#sed -i 's/.*PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config

# Enable ssh
touch /boot/ssh

# Disable Bluetooth
systemctl disable bluetooth.service
cat >> /boot/config.txt <<EOF
enable_uart=1
dtoverlay=disable-bt
EOF

# Disable apt-daily timers & kill services
systemctl stop apt-daily.timer
systemctl stop apt-daily-upgrade.timer
systemctl disable apt-daily.timer
systemctl disable apt-daily-upgrade.timer
#killService apt-daily.service
#killService apt-daily-upgrade.service

export DEBIAN_FRONTEND=noninteractive

# Set retries for apt
echo "APT::Acquire::Retries \"5\";" > /etc/apt/apt.conf.d/80-retries

# Default samba install options
echo "samba-common samba-common/workgroup string WORKGROUP" | debconf-set-selections
echo "samba-common samba-common/dhcp boolean true" | debconf-set-selections
echo "samba-common samba-common/do_debconf boolean true" | debconf-set-selections

# Remove classic networking & setup/enable systemd-resolved/networkd
# https://raspberrypi.stackexchange.com/questions/89803/access-point-as-wifi-router-repeater-optional-with-bridge
apt -y update
#apt -y upgrade
apt -y --autoremove purge ifupdown dhcpcd5 isc-dhcp-client isc-dhcp-common rsyslog avahi-daemon
apt-mark hold ifupdown dhcpcd5 isc-dhcp-client isc-dhcp-common rsyslog raspberrypi-net-mods openresolv avahi-daemon libnss-mdns
apt -y install libnss-resolve hostapd dnsmasq samba git python3 python3-pip
rm -rf /etc/network /etc/dhcp
systemctl enable systemd-networkd.service systemd-resolved.service
systemctl unmask hostapd.service
systemctl enable hostapd.service

# Setup hostapd
cat > /etc/hostapd/hostapd.conf <<EOF
interface=ap0
driver=nl80211
ssid=${AP_SSID}
country_code=US
hw_mode=g
channel=1
auth_algs=1
wpa=2
wpa_passphrase=${AP_PASS}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
bridge=br0
EOF
chmod 600 /etc/hostapd/hostapd.conf

cp /lib/systemd/system/hostapd.service /etc/systemd/system/hostapd.service
sed -i 's/After=/#After=/g' /etc/systemd/system/hostapd.service

#SYSTEMD_EDITOR=tee systemctl edit hostapd.service <<EOF
mkdir -p /etc/systemd/system/hostapd.service.d
cat > /etc/systemd/system/hostapd.service.d/override.conf <<EOF
[Unit]
Wants=wpa_supplicant@wlan0.service

[Service]
Restart=no
ExecStartPre=/sbin/iw dev wlan0 interface add ap0 type __ap
ExecStopPost=-/sbin/iw dev ap0 del
EOF

# Configs for AP0 (Picobrew Devices) + WLAN0 (Internet)
cp /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant-wlan0.conf
chmod 600 /etc/wpa_supplicant/wpa_supplicant-wlan0.conf
systemctl disable wpa_supplicant.service
systemctl enable wpa_supplicant@wlan0.service
rfkill unblock 0

#SYSTEMD_EDITOR=tee systemctl edit wpa_supplicant@wlan0.service <<EOF
mkdir -p /etc/systemd/system/wpa_supplicant@wlan0.service.d
cat > /etc/systemd/system/wpa_supplicant@wlan0.service.d/override.conf <<EOF
[Unit]
BindsTo=hostapd.service
After=hostapd.service
Wants=ap-bring-up.service
Before=ap-bring-up.service

[Service]
ExecStopPost=-/bin/ip link set ap0 up
EOF

# Setup ap-bring-up
cat > /etc/systemd/system/ap-bring-up.service <<EOF
[Unit]
Description=Bring up wifi interface ap0
Requisite=hostapd.service

[Service]
Type=oneshot
ExecStart=/lib/systemd/systemd-networkd-wait-online --interface=wlan0 --timeout=60 --quiet
ExecStartPost=/bin/ip link set ap0 up
ExecStartPost=/usr/bin/resolvectl dnssec ap0 no
EOF

# Setup br0
cat > /etc/systemd/network/02-br0.netdev <<EOF
[NetDev]
Name=br0
Kind=bridge
EOF

# Setup eth0
cat > /etc/systemd/network/04-eth0.network <<EOF
[Match]
Name=eth0
[Network]
DNSSEC=no
Bridge=br0
EOF

# Setup wlan0
cat > /etc/systemd/network/08-wlan0.network <<EOF
[Match]
Name=wlan0
[Network]
DNSSEC=no
DHCP=yes
EOF

cat > /etc/systemd/network/16-br0_up.network <<EOF
[Match]
Name=br0
[Network]
DNSSEC=no
IPMasquerade=yes
Address=${AP_IP}/24
DHCPServer=yes
[DHCPServer]
DNS=${AP_IP}
EOF

# Disable resolved DNS stub listener & point to localhost (dnsmasq) 
sed -i 's/.*DNSStubListener=.*/DNSStubListener=no/g' /etc/systemd/resolved.conf
sed -i 's/.*IGNORE_RESOLVCONF.*/IGNORE_RESOLVCONF=yes/g' /etc/default/dnsmasq

# Setup dnsmasq
cat >> /etc/dnsmasq.conf <<EOF
address=/picobrew.com/127.0.0.1
server=8.8.8.8
server=8.8.4.4
EOF

# Add picobrew to /etc/hosts
cat >> /etc/hosts <<EOF
${AP_IP}       picobrew.com
EOF

# Setup Samba
cat > /etc/samba/smb.conf <<EOF
[global]
workgroup = WORKGROUP
server string = Samba Server
netbios name = PICOBREW_SERVER
security = user
map to guest = Bad User
guest account = root
dns proxy = no

[App]
guest ok = yes
path = /picobrew_pico
available = yes
browsable = yes
public = yes
writable = yes
read only = no

[Recipes]
guest ok = yes
path = /picobrew_pico/app/recipes
available = yes
browsable = yes
public = yes
writable = yes
read only = no

[History]
guest ok = yes
path = /picobrew_pico/app/sessions
available = yes
browsable = yes
public = yes
writable = yes
read only = no
EOF
service smbd restart

# Startup Script
sed -i 's/exit 0//g' /etc/rc.local
cat >> /etc/rc.local <<EOF
if [ ! -d "/picobrew_pico" ]
then
  echo 'Installing Picobrew Server...'
  cd /
  git clone https://github.com/chiefwigms/picobrew_pico.git
  cd /picobrew_pico
  git update-index --assume-unchanged config.yaml
  pip3 install -r requirements.txt
else
  echo 'Updating Picobrew Server...'
  cd /picobrew_pico
  git pull
  pip3 install -r requirements.txt
fi
echo 'Starting Picobrew Server...'
python3 server.py &

exit 0
EOF

# Re-enable apt-daily timers
#systemctl enable apt-daily.timer
#systemctl enable apt-daily-upgrade.timer

reboot
