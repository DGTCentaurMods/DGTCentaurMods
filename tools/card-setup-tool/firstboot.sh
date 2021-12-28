#!/bin/bash 
echo $(date +"%T") "sleep 60seconds" >>/boot/centaur_install.log
sleep 60
echo $(date +"%T") "apt update" >>/boot/centaur_install.log
apt update
echo $(date +"%T")  "apt -y upgrade" >>/boot/centaur_install.log
apt -y upgrade
echo $(date +"%T")  "apt -y full-upgrade" >>/boot/centaur_install.log
apt -y full-upgrade
echo $(date +"%T")  "apt -y install /boot/DGTCentaurMods" >>/boot/centaur_install.log
apt -y install /boot/DGTCentaurMods_0-build_armhf.deb
echo $(date +"%T")  "disable firstboot.service" >>/boot/centaur_install.log
systemctl disable firstboot.service 
echo $(date +"%T")  "remove /etc/systemd/system/firstboot.service" >>/boot/centaur_install.log
rm -rf /etc/systemd/system/firstboot.service
echo $(date +"%T")  "remove /home/pi/firstboot.sh" >>/boot/centaur_install.log
rm -f /home/pi/firstboot.sh
echo $(date +"%T")  "reboot 2" >>/boot/centaur_install.log
reboot



