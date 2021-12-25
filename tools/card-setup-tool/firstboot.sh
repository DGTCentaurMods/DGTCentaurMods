#!/bin/bash 
apt get update
apt get -y upgrade
apt get -y full-upgrade
apt -y install /boot/DGTCentaurMods_0-build_armhf.deb

systemctl disable firstboot.service 
rm -rf /etc/systemd/system/firstboot.service
rm -f /home/pi/firstboot.sh
reboot