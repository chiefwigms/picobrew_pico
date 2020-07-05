Creating a custom image:
Download lastest Lite image from https://www.raspberrypi.org/downloads/raspberry-pi-os/
Download firstboot.service from https://github.com/nmcclain/raspberian-firstboot
(Remove ExecStartPost from firstboot.service - script will rename itself)
Extract img from zip
Optional:
  For offline-ish install (vanilla image on sd card):
    apt-get -y install --print-uris <packages> | cut -d\' -f2 | grep http:// > debs2dl
    wget -i debs2dl
    dpkg -i *.deb

mkdir mnt boot
losetup -P /dev/loop0 <image>
mount /dev/loop0p2 ./mnt
cp <firstboot.service> ./mnt/lib/systemd/system/
cd ./mnt/etc/systemd/system/multi-user.target.wants
ln -s /lib/systemd/system/firstboot.service .
chmod 0644 /lib/systemd/system/firstboot.service
cd ..
umount mnt
mount /dev/loop0p1 ./boot
cp <firstboot.sh> boot
cp <ssh> ./boot
cp <wpa_supplicant.conf> ./boot
umount boot
losetup -D
