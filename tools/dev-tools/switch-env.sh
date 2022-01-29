#!/usr/bin/bash

BASE="$(pwd)/../.."
PCK_NAME="DGTCentaurMods"
INSTALL_DIR=/home/pi
SERVICES=(DGTCentaurMods.service centaurmods-web.service)

function restartServices {
    echo -e "Restarting services"
    for service in ${SERVICES[@]}; do
        echo -e "--> Restarting $service"
        sudo systemctl restart $service
    done
}


function moveEnginesFolder {
    if [ -d ${INSTALL_DIR}/.${PCK_NAME}/engines ]; then
        read -p "Do you want to link engines too? (y/n): "
        case $REPLY in
            [Yy]* ) 
                echo -e "--> Linking engines folder:
                ${INSTALL_DIR}/.${PCK_NAME}/engines --> ${PCK_NAME}/engines"
                mv ${BASE}/${PCK_NAME}/engines ${BASE}/${PCK_NAME}/.engines
                ln -s ${INSTALL_DIR}/.${PCK_NAME}/engines ${BASE}/${PCK_NAME}/engines
                ;;
            [Nn]* ) break ;; 
            * ) break ;;
        esac
    fi
}


function toggle {
    ### Check if we are already switched
    if [ -e ${BASE}/.toggled ]; then
        echo -e "This repository is live on board in ${INSTALL_DIR}."
        echo -e "Deactivating."
        # Checki if engines are linked.
        cd ${BASE}/${PCK_NAME}
        if [ -d .engines ]; then
            echo -e "-- > Unlinking engines folder..."
            rm engines && mv .engines engines
        fi
        cd ${INSTALL_DIR}
        rm ${PCK_NAME}
        if [ -d .${PCK_NAME} ]; then
            mv .${PCK_NAME} ${PCK_NAME} && rm $BASE/.toggled
        fi
        restartServices
    echo -e "Done. Have a nice day!"
    else
        echo -e "Installing in ${INSTALL_DIR}"
        cd ${INSTALL_DIR}
        if [ -d ${PCK_NAME} ]; then
            mv ${PCK_NAME} .${PCK_NAME}
        fi
        ln -s ${BASE}/${PCK_NAME} && touch ${BASE}/.toggled
        moveEnginesFolder
        restartServices
        echo -e "!!! You are using now a repo as a QA tier. Be careful on your git commits. !!!"
        echo -e "Do not add unnecessary files in your commit."
        echo -e "Done. Bye."
    fi
}


## Main

if [ -e $BASE/.toggled ]; then
    echo -e "Your repository is currently installed in ${INSTALL_DIR}"
else
   echo -e "This repository is not installed."
fi

read -p "Do you want to switch? (y/n): "
case $REPLY in
    [Yy]* ) toggle
            exit 0
            ;;
    [Nn]* ) exit 0
            ;;
esac
