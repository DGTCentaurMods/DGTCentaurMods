#!/usr/bin/bash

source config/build.config

BASEDIR=`pwd`
PACKAGE="DGTCentaurMods"
INSTALLDIR="/opt/${PACKAGE}"
cd ../

function detectVersion {
    echo -e "::: Getting version"
    VERSION=`cat ${PACKAGE}/DEBIAN/control | grep Version | cut -d':' -f2 | cut -c2-`
    return
}

function stage {
    STAGE="dgtcentaurmods_${VERSION}_armhf"
    echo -e "::: Staging build"
    cp -r $(basename "$PWD"/${PACKAGE}) /tmp/${STAGE}
    return
}


function setPermissions {
    echo -e "::: Setting permissions"
    sudo chown root.root /tmp/${STAGE}/etc
    sudo chmod 777 /tmp/${STAGE}/opt/${PACKAGE}/engines
    return
}


function build {
    echo -e "::: Building version ${VERSION}"
    if [ ! -d ${BASEDIR}/releases ]; then mkdir ${BASEDIR}/releases; fi
    dpkg-deb --build /tmp/${STAGE} ${BASEDIR}/releases/${STAGE}.deb
    return
}


function insertStockfish {
    REPLY="Y"
    if [ ! $FULL -eq 1 ]; then
        read -p "Do you want to compile and insert Stockfinsh in this build? (y/n): "
    else
        case $REPLY in
            [Yy]* )
                cd /tmp
                echo -e "Cloning Stockfish repo"  
                git clone $STOCKFISH_REPO
                if [ $(dpkg-query -W -f='${Status}' libsqlite3-dev 2>/dev/null | grep -c "ok installed") -eq 0 ]; then
                    sudo apt-get install libsqlite3-dev;
                fi
                cd Stockfish/src
                make clean
                make -j$(nproc) build ARCH=armv7    

                mv stockfish Stockfish
                cp Stockfish /tmp/${STAGE}${INSTALLDIR}/engines
                return
                ;;
            [Nn]* ) return
                ;;
        esac
    fi
}


function clean {
    echo -e "::: Cleaning"
    sudo rm -rf /tmp/dgtcentaurmods*
    rm -rf ${BASEDIR}/releases
    rm -rf /tmp/Stockfish
}

function removeDev {
    #All files in repo that are used in development stage are removed here
    rm /tmp/${STAGE}/opt/${PACKAGE}/config/centaur.ini
    rm /tmp/${STAGE}/opt/${PACKAGE}/db/centaur.db
}


function main() {
    clean 2>/dev/null
    detectVersion
    stage
    removeDev 2>/dev/null
    setPermissions
    insertStockfish
    build
}


## MAIN ##
case $1 in
    clean* )
        clean
        ;;
    full* )
        FULL=1
        main
        ;;
    * )
        FULL=0
        main
        ;;
esac

exit 0

