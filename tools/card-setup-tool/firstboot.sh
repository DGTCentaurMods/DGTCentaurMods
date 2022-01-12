#!/bin/bash 
#
#This file is part of the DGTCentaur Mods open source software
# ( https://github.com/EdNekebno/DGTCentaur )
#
# DGTCentaur Mods is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# DGTCentaur Mods is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file.  If not, see
#
# https://github.com/EdNekebno/DGTCentaur/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.


echo $(date +"%T") "sleep 5 seconds" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "sleep 5 seconds" >>/boot/centaur_install.log
sleep 5
echo $(date +"%T") "apt update" >>/boot/centaur_install.log
apt update | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "apt -y upgrade" >>/boot/centaur_install.log
apt -y upgrade | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "apt -y full-upgrade" >>/boot/centaur_install.log
apt -y full-upgrade | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "apt -y install /boot/DGTCentaurMods" >>/boot/centaur_install.log
apt -y install /boot/DGTCentaurMods_0-build_armhf.deb | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "disable firstboot.service" >>/boot/centaur_install.log
systemctl disable firstboot.service | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "remove /etc/systemd/system/firstboot.service" >>/boot/centaur_install.log
rm -rfv /etc/systemd/system/firstboot.service | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "remove /home/pi/firstboot.sh" >>/boot/centaur_install.log
rm -rfv /home/pi/firstboot.sh | awk '{ print strftime("%H:%M:%S: "), $0; fflush(); }'>>/boot/centaur_install.log
echo $(date +"%T")  "reboot 2" >>/boot/centaur_install.log
reboot



