#!/bin/bash
# AP for Pico devices
# SSID Must be > 8 Chars
AP_IP="192.168.72.1"
AP_SSID="PICOBREW"
AP_PASS="PICOBREW"

export IMG_NAME="PICOBREW_PICO"
export IMG_RELEASE="beta6"
export IMG_VARIANT="stable"
# export IMG_VARIANT="latest"
export GIT_SHA='$(git rev-parse --short HEAD)'

# Enable root login
#sed -i 's/.*PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config

echo 'Disabling Bluetooth...'
systemctl disable bluetooth.service
cat >> /boot/config.txt <<EOF
enable_uart=1
dtoverlay=disable-bt
EOF

echo 'Load default wpa_supplicant.conf...'
cat > /boot/wpa_supplicant.conf <<EOF
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    # bssid=YO:UR:24:GH:ZB:SS:ID
    ssid="YOUR_WIFI_NAME"
    psk="YOUR_WIFI_PASSWORD"
    key_mgmt=WPA-PSK
    freq_list=2412 2417 2422 2427 2432 2437 2442 2447 2452 2457 2462
}
EOF

echo 'Disabling apt-daily timers...'
systemctl stop apt-daily.timer
systemctl stop apt-daily-upgrade.timer
systemctl disable apt-daily.timer
systemctl disable apt-daily-upgrade.timer

# revert 'stable' image to have rpt4 wireless firmware
# build 'latest' image with the following lines commented out (required for Pi 400 - see https://github.com/chiefwigms/picobrew_pico/issues/182)
if [[ ${IMG_VARIANT} == "stable" ]];
then
    echo 'Revert to stable WiFi firmware...'
    dpkg --purge firmware-brcm80211
    wget http://archive.raspberrypi.org/debian/pool/main/f/firmware-nonfree/firmware-brcm80211_20190114-1+rpt4_all.deb
    dpkg -i firmware-brcm80211_20190114-1+rpt4_all.deb
    apt-mark hold firmware-brcm80211
    rm firmware-brcm80211_20190114-1+rpt4_all.deb
fi

echo 'Updating packages...'
export DEBIAN_FRONTEND=noninteractive
echo "APT::Acquire::Retries \"5\";" > /etc/apt/apt.conf.d/80-retries
echo "samba-common samba-common/workgroup string WORKGROUP" | debconf-set-selections
echo "samba-common samba-common/dhcp boolean true" | debconf-set-selections
echo "samba-common samba-common/do_debconf boolean true" | debconf-set-selections

apt -y update
apt -y upgrade

# https://raspberrypi.stackexchange.com/questions/89803/access-point-as-wifi-router-repeater-optional-with-bridge
echo 'Removing default networking...'
apt -y --autoremove purge ifupdown dhcpcd5 isc-dhcp-client isc-dhcp-common rsyslog avahi-daemon
apt-mark hold ifupdown dhcpcd5 isc-dhcp-client isc-dhcp-common rsyslog raspberrypi-net-mods openresolv avahi-daemon libnss-mdns
echo 'Installing required packages...'
apt -y install libnss-resolve hostapd dnsmasq dnsutils samba git python3 python3-pip nginx openssh-server

echo 'Installing Picobrew Server...'
cd /
git clone https://github.com/chiefwigms/picobrew_pico.git
cd /picobrew_pico
pip3 install -r requirements.txt
cd /

echo 'Setting up WiFi AP + Client...'
rm -rf /etc/network /etc/dhcp
systemctl enable systemd-networkd.service systemd-resolved.service

# Setup hostapd
cat > /etc/hostapd/hostapd.conf <<EOF
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

cat > /etc/systemd/system/accesspoint@.service <<EOF
[Unit]
Description=accesspoint with hostapd (interface-specific version)
Wants=wpa_supplicant@%i.service

[Service]
ExecStartPre=/sbin/iw dev %i interface add ap@%i type __ap
ExecStart=/usr/sbin/hostapd -i ap@%i /etc/hostapd/hostapd.conf
ExecStartPost=/usr/sbin/rfkill unblock wifi wlan
ExecStopPost=-/sbin/iw dev ap@%i del
ExecStopPost=/usr/sbin/rfkill unblock wifi wlan

[Install]
WantedBy=sys-subsystem-net-devices-%i.device
EOF
systemctl disable hostapd.service
systemctl disable wpa_supplicant.service
rm -f /etc/wpa_supplicant/wpa_supplicant.conf
systemctl enable accesspoint@wlan0.service

#SYSTEMD_EDITOR=tee systemctl edit wpa_supplicant@wlan0.service <<EOF
mkdir -p /etc/systemd/system/wpa_supplicant@wlan0.service.d
cat > /etc/systemd/system/wpa_supplicant@wlan0.service.d/override.conf <<EOF
[Unit]
BindsTo=accesspoint@%i.service
After=accesspoint@%i.service

[Service]
ExecStartPost=/lib/systemd/systemd-networkd-wait-online --interface=%i --timeout=60 --quiet
ExecStartPost=/usr/sbin/rfkill unblock wifi wlan
ExecStartPost=/bin/ip link set ap@%i up
ExecStopPost=-/bin/ip link set ap@%i up
ExecStopPost=/usr/sbin/rfkill unblock wifi wlan
EOF

# Overwrite wpa_supplicant.conf (if exists) from boot
cat > /etc/systemd/system/update_wpa_supplicant.service <<EOF
[Unit]
Description=Copy user wpa_supplicant.conf
ConditionPathExists=/boot/wpa_supplicant.conf
Before=ap-bring-up.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/mv /boot/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant-wlan0.conf
ExecStartPost=/bin/chmod 600 /etc/wpa_supplicant/wpa_supplicant-wlan0.conf

[Install]
WantedBy=multi-user.target
EOF
systemctl enable update_wpa_supplicant.service

# Setup static interfaces
cat > /etc/systemd/network/02-br0.netdev <<EOF
[NetDev]
Name=br0
Kind=bridge
EOF

cat > /etc/systemd/network/04-eth0.network <<EOF
[Match]
Name=eth0
[Network]
Bridge=br0
ConfigureWithoutCarrier=yes
EOF

cat > /etc/systemd/network/08-wifi.network <<EOF
[Match]
Name=wl*
[Network]
LLMNR=no
MulticastDNS=no
IPForward=yes
DHCP=yes
EOF

cat > /etc/systemd/network/16-br0_up.network <<EOF
[Match]
Name=br0
[Network]
IPMasquerade=yes
Address=${AP_IP}/24
EOF

echo 'Disable resolved DNS stub listener & point to localhost (dnsmasq)...'
sed -i 's/.*DNSStubListener=.*/DNSStubListener=no/g' /etc/systemd/resolved.conf
sed -i 's/.*IGNORE_RESOLVCONF.*/IGNORE_RESOLVCONF=yes/g' /etc/default/dnsmasq

echo 'Disabling ipv6...'
cat >> /etc/sysctl.conf <<EOF
net.ipv6.conf.all.disable_ipv6=1
net.ipv6.conf.default.disable_ipv6=1
net.ipv6.conf.lo.disable_ipv6=1
net.ipv6.conf.eth0.disable_ipv6 = 1
EOF

echo 'Setting up dnsmasq...'
cat >> /etc/dnsmasq.conf <<EOF
address=/picobrew.com/${AP_IP}
address=/www.picobrew.com/${AP_IP}
server=8.8.8.8
server=8.8.4.4
server=1.1.1.1
interface=br0
  dhcp-range=192.168.72.100,192.168.72.200,255.255.255.0,24h
EOF

echo 'Setting up /etc/hosts...'
cat >> /etc/hosts <<EOF
${AP_IP}       picobrew.com
${AP_IP}       www.picobrew.com
EOF

echo 'Generating self-signed SSL certs...'
mkdir /certs
cat > /certs/req.cnf <<EOF
[v3_req]
keyUsage = critical, digitalSignature, keyAgreement
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
subjectAltName = @alt_names
[alt_names]
DNS.1 = picobrew.com
DNS.2 = www.picobrew.com
EOF

openssl req -x509 -sha256 -newkey rsa:2048 -nodes -keyout /certs/domain.key -days 1825  -out  /certs/domain.crt  -subj "/CN=chiefwigms_Picobrew_Pico CA"

openssl req -newkey rsa:2048 -nodes -subj "/CN=picobrew.com" \
      -keyout  /certs/server.key -out  /certs/server.csr

openssl x509 \
        -CA /certs/domain.crt -CAkey /certs/domain.key -CAcreateserial \
       -in /certs/server.csr \
       -req -days 1825 -out /certs/server.crt -extfile /certs/req.cnf -extensions v3_req

cat /certs/server.crt /certs/domain.crt > /certs/bundle.crt

echo 'Setting up nginx for http and https...'
cat > /etc/nginx/sites-available/picobrew.com.conf <<EOF
server {
    listen 80;
    server_name www.picobrew.com picobrew.com;

    access_log                  /var/log/nginx/picobrew.access.log;
    error_log                   /var/log/nginx/picobrew.error.log;
    
    location / {
        aio threads;

        proxy_set_header    Host \$http_host;
        proxy_pass          http://localhost:8080;
    }

    location /socket.io {
        aio threads;
        
        include proxy_params;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_pass http://localhost:8080/socket.io;
    }
}

server {
    listen 443 ssl;
    server_name www.picobrew.com picobrew.com;

    ssl_certificate             /certs/bundle.crt;
    ssl_certificate_key         /certs/server.key;
    
    access_log                  /var/log/nginx/picobrew.access.log;
    error_log                   /var/log/nginx/picobrew.error.log;
    
    location / {
        aio threads;

        proxy_set_header    Host \$http_host;
        proxy_set_header    X-Real-IP \$remote_addr;
        proxy_set_header    X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Proto \$scheme;
        proxy_pass          http://localhost:8080;
    }
    
    location /socket.io {
        aio threads;
        
        include proxy_params;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_pass http://localhost:8080/socket.io;
    }
}
EOF

ln -s /etc/nginx/sites-available/picobrew.com.conf /etc/nginx/sites-enabled/picobrew.com.conf
rm /etc/nginx/sites-enabled/default

echo 'Setup samba config...'
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

# Have Name Service Switch use DNS
# After resolve install:
# hosts:          files resolve [!UNAVAIL=return] dns
sed -i 's/\(.*hosts:.*\) \[.*\]\(.*\)/\1\2/' /etc/nsswitch.conf

echo 'Setting up rc.local...'
sed -i 's/exit 0//g' /etc/rc.local
cat >> /etc/rc.local <<EOF

# reload systemd manager configuration to recreate entire dependency tree
systemctl daemon-reload

# toggle off WiFi power management on wireless interfaces (wlan0 and ap0)
iw wlan0 set power_save off
iw ap@wlan0 set power_save off

cd /picobrew_pico
if grep -q "update_boot:\s*[tT]rue" config.yaml
then
  echo 'Updating Picobrew Server...'
  git pull || true
  # install dependencies and start server
  pip3 install -r requirements.txt
fi

source_sha=${GIT_SHA}
rpi_image_version=${IMG_RELEASE}_${IMG_VARIANT}

echo "Starting Picobrew Server (image: \${rpi_image_version}; source: \${source_sha}) ..."
python3 server.py 0.0.0.0 8080 &

exit 0
EOF

echo 'Finished custom pi setup!'