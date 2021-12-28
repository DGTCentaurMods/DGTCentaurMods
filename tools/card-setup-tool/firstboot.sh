#!/bin/bash 
echo $(date +"%T") "sleep 5 seconds\n" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds\n" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds\n" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds\n" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds\n" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds\n" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds\n" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds\n" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds\n" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds\n" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds\n" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds\n" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "apt update\n\n" >>/boot/centaur_install.log
apt update | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "apt -y upgrade\n\n" >>/boot/centaur_install.log
apt -y upgrade | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "apt -y full-upgrade\n\n" >>/boot/centaur_install.log
apt -y full-upgrade | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "apt -y install /boot/DGTCentaurMods\n\n" >>/boot/centaur_install.log
apt -y install /boot/DGTCentaurMods_0-build_armhf.deb | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "disable firstboot.service\n\n" >>/boot/centaur_install.log
systemctl disable firstboot.service | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "remove /etc/systemd/system/firstboot.service\n\n" >>/boot/centaur_install.log
rm -rfv /etc/systemd/system/firstboot.service | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "remove /home/pi/firstboot.sh\n\n" >>/boot/centaur_install.log
rm -rfv /home/pi/firstboot.sh | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "reboot 2\n" >>/boot/centaur_install.log
reboot



