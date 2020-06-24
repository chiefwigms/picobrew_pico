#!/bin/sh

SEGMENT=192.168.42
WIFINAME=picobrewers
PASSWORD=12345678

sudo apt-get -y install dnsmasq nginx openssh-server hostapd isc-dhcp-server iptables-persistent

cat <<EOF >> /etc/dhcpcd.conf 
interface wlan0
static ip_address=$SEGMENT.1/24
nohook wpa_supplicant
EOF

cat > /etc/network/interfaces.d/wlan0 <<EOF
iface wlan0 inet static
address $SEGMENT.1
netmask 255.255.255.0
EOF

cat > /etc/network/interfaces.d/eth0 <<EOF
auto eth0
allow-hotplug eth0
iface eth0 inet dhcp
EOF


cat > /etc/nginx/sites-available/picobrew.com.conf <<EOF
server {
        listen 80;
        server_name picobrew.com;
        location / {
        return 301 https://\$host\$request_uri;
        }
}

server {
    listen 443 ssl;
    server_name picobrew.com;
    ssl_certificate           /home/pi/picobrew_pico/certs/bundle.crt;
    ssl_certificate_key       /home/pi/picobrew_pico/certs/server.key;
    #access_log            /var/log/nginx/picobrew.access.log;
    #error_log            /var/log/nginx/picobrew.error.log;

    location / {
	proxy_set_header Host \$http_host;
	proxy_set_header X-Real-IP \$remote_addr;
	proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
	proxy_set_header X-Forwarded-Proto \$scheme;
      	proxy_pass          http://localhost:8080;
    }
  }
EOF

sudo ln -s /etc/nginx/sites-available/picobrew.com.conf /etc/nginx/sites-enabled/picobrew.com.conf
sudo systemctl stop nginx
sudo systemctl start nginx

cat <<EOF >> /etc/dnsmasq.conf
domain-needed
bogus-priv
no-resolv
server=8.8.8.8
server=8.8.4.4
interface=wlan0
interface=eth0
address=/picobrew.com/$SEGMENT.1
EOF

echo "net.ipv4.ip_forward=1" > /etc/sysctl.conf
echo 1 > /proc/sys/net/ipv4/ip_forward

cat <<EOF >> /etc/dhcp/dhcpd.conf 
subnet $SEGMENT.0 netmask 255.255.255.0 {
         range $SEGMENT.10 $SEGMENT.20;
         option broadcast-address $SEGMENT.255;
         option routers $SEGMENT.1;
         option domain-name "local";
         option domain-name-servers $SEGMENT.1, 8.8.8.8, 8.8.4.4;
 }
EOF

cat > /etc/hostapd/hostapd.conf << EOF
ssid=$WIFINAME
wpa_passphrase=$PASSWORD

country_code=US

interface=wlan0
driver=nl80211

wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP

macaddr_acl=0
auth_algs=1

logger_syslog=1
logger_syslog_level=4
logger_stdout=-1
logger_stdout_level=0

wmm_enabled=0

channel=11
EOF

cat <<EOF >> /etc/default/isc-dhcp-server
INTERFACESv4="wlan0"
INTERFACESv6=""
EOF

sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd

sudo update-rc.d hostapd enable
sudo update-rc.d isc-dhcp-server enable

sudo rfkill block bluetooth
sudo rfkill unblock wifi

cd /home/pi/picobrew_pico
sudo pip3 install -r requirements.txt 

/home/pi/picobrew_pico/bin/generate_pki.sh
