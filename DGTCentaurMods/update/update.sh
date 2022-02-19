#!/usr/bin/bash

sleep 5

cd /tmp
sudo apt install -y ./dgtcentaurmods_armhf.deb; sudo apt systemctl start stopDGTController.service
