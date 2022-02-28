#!/usr/bin/bash

# This file is moved outside in /tmp when a new update is available
# It will handle the update process on shutdown.

# Wait for DGTCM to stop
sleep 10

cd /tmp
sudo apt install -y ./dgtcentaurmods_armhf.deb
sudo systemctl start stopDGTController.service
