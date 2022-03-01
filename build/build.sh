#!/usr/bin/bash

source config/build.config

BASEDIR=`pwd`
PACKAGE="DGTCentaurMods"
INSTALLDIR="/opt/${PACKAGE}"
cd ../

function selectBuild {
    #See if this is a git repo
    VERSION=`git branch | grep "*" | cut -f2 -d' '`
    echo -e "::: Checking build type"
    if [ "$VERSION" != "" ]; then
        if [ ${VERSION:0:1} = v ]; then VERSION=${VERSION:0:1}; fi
        return
    else
        VERSION=`basename "$PWD" | cut -c16-`
        if [ ${VERSION:0:1} = v ]; then VERSION=${VERSION:0:1}; fi
        return
    fi
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
    echo -e "::: Building starting"
    if [ ! -d ${BASEDIR}/releases ]; then mkdir ${BASEDIR}/releases; fi
    dpkg-deb --build /tmp/${STAGE} ${BASEDIR}/releases/${STAGE}.deb
    return
}


function insertStockfish {
    read -p "Do you want to compile and insert Stockfinsh in this build? (y/n): "
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

            mv stockfish stockfish_pi
            cp stockfish_pi /tmp/${STAGE}${INSTALLDIR}/engines
            return
            ;;
        [Nn]* ) return
            ;;
    esac
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

## MAIN ##
case $1 in
    clean* )
        clean
        ;;
    *)
        clean 2>/dev/null
        selectBuild
        stage
        removeDev 2>/dev/null
        setPermissions
        insertStockfish
        build
        exit 0
        ;;
esac

