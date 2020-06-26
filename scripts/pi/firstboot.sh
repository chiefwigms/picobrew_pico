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
apt -y install libnss-resolve hostapd dnsmasq dnsutils samba git python3 python3-pip nginx openssh-server

# Install Picobrew server
cd /
git clone https://github.com/chiefwigms/picobrew_pico.git
cd /picobrew_pico
git update-index --assume-unchanged config.yaml
pip3 install -r requirements.txt
cd /

# Setup Hostapd
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
address=/picobrew.com/${AP_IP}
address=/www.picobrew.com/${AP_IP}
server=8.8.8.8
server=8.8.4.4
EOF

# Add picobrew to /etc/hosts
cat >> /etc/hosts <<EOF
${AP_IP}       picobrew.com
${AP_IP}       www.picobrew.com
EOF

# Generate self-signed SSL certs
mkdir /certs
cat > /certs/req.cnf <<EOF
[v3_req]
keyUsage = critical, digitalSignature, keyAgreement
extendedKeyUsage = serverAuth
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

# Setup nginx for http and https
cat > /etc/nginx/sites-available/picobrew.com.conf <<EOF
server {
    listen 80;
    server_name www.picobrew.com picobrew.com;
    
    location / {
        proxy_set_header    Host \$http_host;
        proxy_pass          http://localhost:8080;
    }

    location /socket.io {
        include proxy_params;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
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
        proxy_set_header    Host \$http_host;
        proxy_set_header    X-Real-IP \$remote_addr;
        proxy_set_header    X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Proto \$scheme;
        proxy_pass          http://localhost:8080;
    }

    location /socket.io {
        include proxy_params;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_pass http://localhost:8080/socket.io;
    }
  }
EOF
ln -s /etc/nginx/sites-available/picobrew.com.conf /etc/nginx/sites-enabled/picobrew.com.conf
systemctl stop nginx
systemctl start nginx

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
if [ -d "/picobrew_pico" ]
then
  echo 'Updating Picobrew Server...'
  cd /picobrew_pico
  git pull
  pip3 install -r requirements.txt
  echo 'Starting Picobrew Server...'
  python3 server.py 0.0.0.0 8080 &
fi

exit 0
EOF

# Re-enable apt-daily timers
#systemctl enable apt-daily.timer
#systemctl enable apt-daily-upgrade.timer

# Rename script
mv /boot/firstboot.sh /boot/firstboot.done

echo "Finished setup - rebooting now!"
reboot
