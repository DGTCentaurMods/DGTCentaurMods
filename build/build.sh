#!/usr/bin/bash

# Script to produce deb pacjage

##### VARIABLESi
REPO_NAME="DGTCentaur"
REPO_URL="https://github.com/EdNekebno/DGTCentaur"

function build {
    dpkg-deb --build ${REPO_NAME}_${TAG}_armhf
}

function edit_control {
    sed -i "s/Version:.*/Version: $TAG/g" control
    cp control ${REPO_NAME}_${TAG}_armhf/DEBIAN
    build
}
function stage {
    mkdir ${REPO_NAME}_${TAG}_armhf
    mkdir -p ${REPO_NAME}_${TAG}_armhf/DEBIAN ${REPO_NAME}_${TAG}_armhf/home/pi ${REPO_NAME}_${TAG}_armhf/etc/systemd/system
    
    # Move system services
    mv $REPO_NAME/${REPO_NAME}Mods/etc/* ${REPO_NAME}_${TAG}_armhf/etc/systemd/system
    
    # Removed unnecessary stuff
    rm -rf $REPO_NAME/${REPO_NAME}Mods/etc
    rm $REPO_NAME/*.md

    # Move main software in /home/pi
    mv $REPO_NAME/${REPO_NAME}Mods ${REPO_NAME}_${TAG}_armhf/home/pi
    mv $REPO_NAME/requirements.txt ${REPO_NAME}_${TAG}_armhf/home/pi/{REPO_NAME}Mods

    # Set permissions
    sudo chown -R root.root ${REPO_NAME}_${TAG}_armhf/etc/systemd/system

    # Remove files from Git
    rm -rf $REPO_NAME
    
    edit_control
}


function build_release {
if [ -x $1 ]
then
    TAG="0"
    # Clean any existing data
    if [ -d ${REPO_NAME}_${TAG}_arm ]
    then
        sudo rm -rf ${REPO_NAME}_${TAG}
    fi
    git clone --depth 1 $REPO_URL && stage
else
    TAG=$1
    git clone --depth 1 --branch $TAG $REPO_URL --single-branch && stage
fi  
}

##### START ###

case $1 in
    master* )  build_release; exit;;
esac
        read -p "Is this a release from master (Y/N(: "
        case $REPLY in
            [Yy]* ) build_release;;
            [Nn]* ) 
                read -p "Please input release number: "
                build_release $REPLY
                ;;
            * ) echo "Please answer yes or no.";;
     
   
    esac
