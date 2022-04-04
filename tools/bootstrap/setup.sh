#!/usr/bin/bash
#
# Bootstrap installer for Linux
#

VERSION="1.1.4"

echo -e "This setup will install the latest release ($VERSION).\nIf you want to install a different version, please specify.\n"
read -p "Please input what release you want to install ($VERSION): "
if [ ! -z $REPLY ]; then
    VERSION=$REPLY
fi
URL="https://github.com/EdNekebno/DGTCentaurMods/releases/download/v${VERSION}/dgtcentaurmods_${VERSION}_armhf.deb"
FILE="dgtcentaurmods_${VERSION}_armhf.deb"

echo -e "::: Downloading DGTCentaurMods v${VERSION}"
wget $URL
echo -e "::: Starting install"
sudo apt install -y ./${FILE}
rm $FILE
echo -e "\n::: Rebooting"
sudo reboot

