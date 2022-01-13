#!/usr/bin/sh

# Check if pip is installed
if sudo dpkg -l | grep -q python3-pip
then
    echo "::: Pip is installed."
else
    echo "::: Pip not installed. Installing now..."
    sudo apt-get install -y python3-pip
fi

# Check if virtualenv is installe
if sudo pip3 list | grep virtualenv
then
    echo "::: Virtualenv is installed."
else
   echo "::: Virtualenv missing, Installing..."
   sudo pip3 install virtualenv
fi

# Deploy python environment
cd ../../..
echo "::: Deploying python env..."
virtualenv .venv

echo "::: Installing packages inside the environment..."
CFLAGS="-fcommon" .venv/bin/pip3 install -r requirements.txt

echo "::: All done."
echo ":: Activate environment using \"source .venv/bin/activate\""

