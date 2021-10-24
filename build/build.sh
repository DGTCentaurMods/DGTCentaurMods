#!/usr/bin/bash

# Script to produce deb pacjage

##### VARIABLESi
BASE=`pwd`
REPO_NAME="DGTCentaur"
REPO_URL="https://github.com/EdNekebno/DGTCentaur"
PCK_NAME="DGTCentaurMods"
SETUP_DIR="/home/pi"

function build {
    dpkg-deb --build ${STAGE}
}

function config_setup {
    sed -i "s/Version:.*/Version: $TAG/g" control
    
    cd ${STAGE}/etc/systemd/system
        SETUP_DIR=$(sed 's/[^a-zA-Z0-9]/\\&/g' <<<"$SETUP_DIR")
        
        # Setup DGT Centaur Mods service
        echo "::: Configuring service:  DGTCentaurMods.service"
            sed -i "s/ExecStart.*/ExecStart=python3.7 game\/menu.py/g" DGTCentaurMods.service
            sed -i "s/WorkingDirectory.*/WorkingDirectory=${SETUP_DIR}\/${PCK_NAME}/g" DGTCentaurMods.service
            sed -i "s/Environment.*/Environment=\"PYTHONPATH=${SETUP_DIR}\"/g" DGTCentaurMods.service
        
        # Setup web service
        echo "::: Configuring service: centaurmods-web.service"
            sed -i "s/WorkingDirectory.*/WorkingDirectory=${SETUP_DIR}\/${PCK_NAME}\/web/g" centaurmods-web.service
            sed -i "s/Environment.*/Environment=\"PYTHONPATH=${SETUP_DIR}\"/g" centaurmods-web.service
        
    cd $BASE
    # Setup postinst file
        echo "::: Configuring postinst."
        sed -i "s/^SETUP_DIR.*/SETUP_DIR=${SETUP_DIR}\/${PCK_NAME}/g" postinst
        sed -i "s/^CENTAURINI.*/CENTAURINI=${SETUP_DIR}\/${PCK_NAME}\/config\/centaur.ini/g" postinst

    cp control ${STAGE}/DEBIAN
    cp postinst ${STAGE}/DEBIAN
    # Set permissions
    sudo chown -R root.root ${STAGE}/etc

    build
}
function stage {
    STAGE="${PCK_NAME}_${TAG}_armhf"
    mkdir ${STAGE}
    mkdir -p ${STAGE}/DEBIAN ${STAGE}/${SETUP_DIR} ${STAGE}/etc/systemd/system
    
    # Move system services
    mv $REPO_NAME/${PCK_NAME}/etc/* ${STAGE}/etc/systemd/system
    
    # Removed unnecessary stuff
    rm -rf $REPO_NAME/${PCK_NAME}/etc
    rm $REPO_NAME/*.md

    # Move main software in /home/pi
    mv $REPO_NAME/${PCK_NAME} ${STAGE}/${SETUP_DIR}
    mv $REPO_NAME/requirements.txt ${STAGE}/${SETUP_DIR}/${PCK_NAME}

    # Remove files from Git
    rm -rf $REPO_NAME
    
    config_setup
}


function build_release {
if [ -x $1 ]
then
    TAG="0"
    # Clean any existing data
    if [ -d ${STAGE} ]
    then
        sudo rm -rf ${STAGE}
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
    clean* ) 
        sudo rm -rf ${REPO_NAME}
        sudo rm -rf  ${PCK_NAME}*
        exit 0
        ;;
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
