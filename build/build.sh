#!/usr/bin/bash
set -e
# Script to produce deb pacjage

##### VARIABLES
BASE=`pwd`
REPO_NAME="DGTCentaur"
REPO_URL="https://github.com/EdNekebno/DGTCentaur"
PCK_NAME="DGTCentaurMods"
SETUP_DIR="/home/pi"
STOCKFISH_REPO="https://github.com/wormstein/Stockfish"


function build {
    dpkg-deb --build ${STAGE}
}

function insertStockfish {
    if [ ! -d Stockfish ] 
    then

        git clone $STOCKFISH_REPO

        cd Stockfish/src
            make clean
            #make map
            make -j$(nproc) build ARCH=armv7

            mv stockfish stockfish_pi
            cp stockfish_pi ${BASE}/${STAGE}/${SETUP_DIR}/${PCK_NAME}/engines
        
        cd $BASE
    else 
        read -p "DO you want to rebuild Stockfish (y/n):"
        case $REPLY in
        [Yy]* ) rm -rf Stockfish && insertStockfish;;
        Nn]* )  cp stockfish_pi ${BASE}/${STAGE}/${SETUP_DIR}/${PCK_NAME}/engines && echo "::: Move on";;
        esac  
        
    fi
}




function configSetup {
    sed -i "s/Version:.*/Version: $TAG/g" control
    
    cd ${STAGE}/etc/systemd/system
        local SETUP_DIR=$(sed 's/[^a-zA-Z0-9]/\\&/g' <<<"$SETUP_DIR")
        
        # Setup DGT Centaur Mods service
        echo "::: Configuring service:  DGTCentaurMods.service"
            sed -i "s/ExecStart.*/ExecStart=python3 game\/menu.py/g" DGTCentaurMods.service
            sed -i "s/WorkingDirectory.*/WorkingDirectory=${SETUP_DIR}\/${PCK_NAME}/g" DGTCentaurMods.service
            sed -i "s/Environment.*/Environment=\"PYTHONPATH=${SETUP_DIR}\"/g" DGTCentaurMods.service
        
        # Setup web service
        echo "::: Configuring service: centaurmods-web.service"
            sed -i "s/WorkingDirectory.*/WorkingDirectory=${SETUP_DIR}\/${PCK_NAME}\/web/g" centaurmods-web.service
            sed -i "s/Environment.*/Environment=\"PYTHONPATH=${SETUP_DIR}\"/g" centaurmods-web.service
        
    cd $BASE
    # Setup postinst file
        echo "::: Configuring postinst."
        sed -i "s/^SETUP_DIR.*/SETUP_DIR=\"${SETUP_DIR}\/${PCK_NAME}\"/g" postinst
        sed -i "s/^CENTAURINI.*/CENTAURINI=${SETUP_DIR}\/${PCK_NAME}\/config\/centaur.ini/g" postinst

    cp control ${STAGE}/DEBIAN
    cp postinst ${STAGE}/DEBIAN
 
    # Set permissions
    sudo chown -R root.root ${STAGE}/etc
    sudo chmod 777 ${STAGE}/home/pi/DGTCentaurMods/engines

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
}


function gitCheckout {
if [ -x $1 ]
then
    TAG="0"
    # Clean any existing data
    if [ -d ${STAGE} ]
    then
        sudo rm -rf ${STAGE}
    fi
    git clone --depth 1 $REPO_URL && stage || exit 1

else
    TAG=$1
    git clone --depth 1 --branch $TAG $REPO_URL --single-branch && stage || exit 1
fi
}

##### START ###

case $1 in
    master* )  gitCheckout;;
    clean* ) 
        sudo rm -rf ${REPO_NAME}
        sudo rm -rf  ${PCK_NAME}*
        rm -rf Stockfish
        exit 0
        ;;
esac
    if [[ -z $1 ]]
    then
        read -p "Is this a release from master (Y/N(: "
        case $REPLY in
            [Yy]* ) gitCheckout;;
            [Nn]* ) 
                read -p "Please input release number: "
                gitCheckout $REPLY
                ;;
            * ) echo "Please answer a tag number"; exit 1;;
        esac
    fi
       
configSetup

read -p "DO you want to integrate Stockfish for this build? (y/n):"
case $REPLY in
    [Yy]* ) insertStockfish;;
    Nn]* ) echo "::: Move on";;
esac


echo "::: Build starting"
build
