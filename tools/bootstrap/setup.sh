#!/usr/bin/bash
#
# Bootstrap installer for Linux
#

VERSION="1.3.0"
URL="https://github.com/EdNekebno/DGTCentaurMods/releases/download/v${VERSION}/dgtcentaurmods_${VERSION}_armhf.deb"
FILE="dgtcentaurmods_${VERSION}_armhf.deb"

echo -e "::: Downloading DGTCentaurMods v${VERSION}"
wget $URL
echo -e "::: Starting install"
sudo apt install -y ./${FILE}
rm $FILE
echo -e "\n::: Rebooting"
sudo reboot

