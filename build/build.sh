#!/usr/bin/bash
#
#This is a tool to build deb packages.
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
    if [ ! -f ./Stockfish/src/stockfish_pi ] 
    then
        if [ ! -d Stockfish ]
        then
            git clone $STOCKFISH_REPO
        fi
        if [ $(dpkg-query -W -f='${Status}' libsqlite3-dev 2>/dev/null | grep -c "ok installed") -eq 0 ];
        then
            sudo apt-get install libsqlite3-dev;
        fi
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
        [Nn]* )  cp ./Stockfish/src/stockfish_pi ${BASE}/${STAGE}/${SETUP_DIR}/${PCK_NAME}/engines && echo "::: Move on";;
        esac  
        
    fi
}




function configSetup {
    sed -i "s/Version:.*/Version: $VERSION/g" DEBIAN/control
    
    cd ${STAGE}/etc/systemd/system
        local SETUP_DIR=$(sed 's/[^a-zA-Z0-9]/\\&/g' <<<"$SETUP_DIR")
        
        # Setup DGT Centaur Mods service
        echo "::: Configuring service:  DGTCentaurMods.service"
            sed -i "s/ExecStart=.*/ExecStart=python3 game\/menu.py/g" DGTCentaurMods.service
            sed -i "s/WorkingDirectory=.*/WorkingDirectory=${SETUP_DIR}\/${PCK_NAME}/g" DGTCentaurMods.service
            sed -i "s/Environment=.*/Environment=\"PYTHONPATH=${SETUP_DIR}\"/g" DGTCentaurMods.service
        
        # Setup web service
        echo "::: Configuring service: centaurmods-web.service"
            sed -i "s/WorkingDirectory=.*/WorkingDirectory=${SETUP_DIR}\/${PCK_NAME}\/web/g" centaurmods-web.service
            sed -i "s/Environment=.*/Environment=\"PYTHONPATH=${SETUP_DIR}\"/g" centaurmods-web.service
        
    cd $BASE
    # Setup postinst file
        echo "::: Configuring postinst."
        sed -i "s/^SETUP_DIR.*/SETUP_DIR=\"${SETUP_DIR}\/${PCK_NAME}\"/g" DEBIAN/postinst
        sed -i "s/^CENTAURINI.*/CENTAURINI=${SETUP_DIR}\/${PCK_NAME}\/config\/centaur.ini/g" DEBIAN/postinst
    
    cp -r DEBIAN ${STAGE}/
 
    # Set permissions
    sudo chown -R root.root ${STAGE}/etc
    sudo chmod 777 ${STAGE}/home/pi/DGTCentaurMods/engines

}


function stage {
    STAGE="${PCK_NAME}_${FILEVERSION}_armhf"
    mkdir ${STAGE}
    mkdir -p ${STAGE}/DEBIAN ${STAGE}/${SETUP_DIR} 
    
    # Move system services
    mv -v $REPO_NAME/build/system/* ${STAGE}/
    
    # Removed unnecessary stuff
    #rm -rf $REPO_NAME/${PCK_NAME}/etc
    rm  $REPO_NAME/*.md

    # Move main software in /home/pi
    mv  $REPO_NAME/${PCK_NAME} ${STAGE}/${SETUP_DIR}
    mv  $REPO_NAME/requirements.txt ${STAGE}/${SETUP_DIR}/${PCK_NAME}

    # Remove files from Git
    rm -rfv $REPO_NAME
}



function buildLocal {
    VERSION=0-local-$(git branch | grep "*" | cut -f2 -d' ')
    FILEVERSION=local-$(git branch | grep "*" | cut -f2 -d' ')
    cp -r $(pwd)/../../${REPO_NAME} /tmp//${REPO_NAME}
    REPO_NAME="/tmp/${REPO_NAME}"
    stage
}



function gitCheckout {
if [ $1 = master ]
then
    VERSION="0"
    FILEVERSION="master"
    # Clean any existing data
    if [ -d ${STAGE} ]
    then
        sudo rm -rf ${STAGE}
    fi
    echo clone --depth 1 $REPO_URL
    git clone --depth 1 $REPO_URL && stage || exit 1

else
    if [ $2 = branch ]
    then
        VERSION=0-$1
        FILEVERSION=$1
        TAG=$1
    else
        TAG=$1
        VERSION=$1
	FILEVERSION=$1
        echo $TAG $VERSION
    fi
    echo clone --depth 1 --branch $TAG $REPO_URL --single-branch
    git clone --depth 1 --branch $TAG $REPO_URL --single-branch && stage || exit 1
fi
}

##### START ###
if [ ! -z $2 ] 
then
REPO_URL="https://github.com/$2/DGTCentaur"
fi
case $1 in
    master* )  gitCheckout master;;
    clean* ) 
        #sudo rm -rf ${REPO_NAME}
        sudo rm -rf  ${PCK_NAME}*
        rm -rf Stockfish
        exit 0
        ;;
    local* ) buildLocal;;
    * )
        if [[ -z $1 ]]
        then
            read -p "Please enter a tag number: "
            gitCheckout $REPLY
        else
            gitCheckout $1 branch
        fi
        ;;
    esac

configSetup

read -p "DO you want to integrate Stockfish for this build? (y/n):"
case $REPLY in
    [Yy]* ) insertStockfish;;
    [Nn]* ) echo "::: Move on";;
esac


echo "::: Build starting"
build
