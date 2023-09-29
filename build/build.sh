#!/usr/bin/bash

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
    STAGE="DGTCentaurMods_A.alpha-ON${VERSION}"
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

function clean {
    echo -e "::: Cleaning"
    sudo rm -rf /tmp/${STAGE}*
    rm -rf ${BASEDIR}/releases
    rm -rf /tmp/Stockfish
}

function removeDev {
    #All files in repo that are used in development stage are removed here
    rm /tmp/${STAGE}/opt/${PACKAGE}/config/centaur.ini
    rm /tmp/${STAGE}/opt/${PACKAGE}/db/centaur.db

    rm -fr /tmp/${STAGE}/opt/DGTCentaurMods/engines/maia_weights
    rm -fr /tmp/${STAGE}/opt/DGTCentaurMods/engines/personalities
    rm -fr /tmp/${STAGE}/opt/DGTCentaurMods/engines/books
    rm -fr /tmp/${STAGE}/node.js

    find /tmp/${STAGE} -name '.DS_Store' -type f -delete
    find /tmp/${STAGE} -name 'fen.log' -type f -delete
    
    py3clean /tmp/${STAGE} 
}


function main() {
    clean 2>/dev/null
    detectVersion
    stage
    removeDev 2>/dev/null
    setPermissions
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

