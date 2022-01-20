LOCAL_REPO=$(dirname $(dirname $PWD))
PCK_NAME="DGTCentaurMods"
SETUP_DIR="/home/pi"

function toggleDebian {
# Setup DGT Centaur Mods service
echo "::: Configuring service:  DGTCentaurMods.service"
sudo sed -i "s,WorkingDirectory=.*,WorkingDirectory=${SETUP_DIR}/${PCK_NAME},g" /etc/systemd/system/DGTCentaurMods.service
sudo sed -i "s,Environment=.*,Environment=\"PYTHONPATH=${SETUP_DIR}\",g" /etc/systemd/system/DGTCentaurMods.service
        
# Setup web service
echo "::: Configuring service: centaurmods-web.service"
sudo sed -i "s,WorkingDirectory=.*,WorkingDirectory=${SETUP_DIR}/${PCK_NAME}/web,g" /etc/systemd/system/centaurmods-web.service
sudo sed -i "s,Environment=.*,Environment=\"PYTHONPATH=${SETUP_DIR}\",g" /etc/systemd/system/centaurmods-web.service
        
echo "::: Configuring service: stopDGTController.service"
sudo sed -i "s,WorkingDirectory=.*,WorkingDirectory=${SETUP_DIR}/${PCK_NAME},g" /etc/systemd/system/stopDGTController.service
sudo sed -i "s,ExecStart=.*,ExecStart=python3 board/shutdown.py,g" /etc/systemd/system/stopDGTController.service
sudo sed -i "s,Environment=.*,Environment=\"PYTHONPATH=${SETUP_DIR}\",g"	/etc/systemd/system/stopDGTController.service
sudo rm -rf /usr/lib/python3/dist-packages/DGTCentaurMods
sudo ln -s ${SETUP_DIR}/${PCK_NAME} /usr/lib/python3/dist-packages/DGTCentaurMods

}

function toggleLocalRepo {
# Setup DGT Centaur Mods service
echo "::: Configuring service:  DGTCentaurMods.service"
sudo sed -i "s,WorkingDirectory=.*,WorkingDirectory=${LOCAL_REPO}/${PCK_NAME},g" /etc/systemd/system/DGTCentaurMods.service
sudo sed -i "s,Environment=.*,Environment=\"PYTHONPATH=${LOCAL_REPO}\",g" /etc/systemd/system/DGTCentaurMods.service
        
# Setup web service
echo "::: Configuring service: centaurmods-web.service"
sudo sed -i "s,WorkingDirectory=.*,WorkingDirectory=${LOCAL_REPO}/${PCK_NAME}/web,g" /etc/systemd/system/centaurmods-web.service
sudo sed -i "s,Environment=.*,Environment=\"PYTHONPATH=${LOCAL_REPO}\",g" /etc/systemd/system/centaurmods-web.service
        
echo "::: Configuring service: stopDGTController.service"
sudo sed -i "s,WorkingDirectory=.*,WorkingDirectory=${LOCAL_REPO}/${PCK_NAME},g" /etc/systemd/system/stopDGTController.service
sudo sed -i "s,ExecStart=.*,ExecStart=python3 board/shutdown.py,g" /etc/systemd/system/stopDGTController.service
sudo sed -i "s,Environment=.*,Environment=\"PYTHONPATH=${LOCAL_REPO}\",g"	/etc/systemd/system/stopDGTController.service
sudo rm -rf /usr/lib/python3/dist-packages/DGTCentaurMods
sudo ln -s ${LOCAL_REPO}/${PCK_NAME} /usr/lib/python3/dist-packages/DGTCentaurMods

}



echo "You can toggle services between debian install and your local branch"
echo "1 - debian install ${SETUP_DIR}/${PCK_NAME}"
echo "2 - local repo     ${LOCAL_REPO}/${PCK_NAME}"
read -p "choose 1 or 2?:"
case $REPLY in
    [1]* ) toggleDebian;;
    [2]* ) toggleLocalRepo;;
esac

#cat /etc/systemd/system/DGTCentaurMods.service
#cat /etc/systemd/system/centaurmods-web.service
#cat /etc/systemd/system/stopDGTController.service

sudo systemctl daemon-reload
sudo systemctl restart DGTCentaurMods
sudo systemctl restart centaurmods-web

