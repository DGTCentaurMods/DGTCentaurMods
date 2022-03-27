#!/usr/bin/bash

#GIT_TOKEN=Create a .git_passwd file with this variable
    if [ -e .git_token ]; then source .git_token 
    else echo "No .git_token file"; exit 1; fi

BASEDIR=`pwd`

REPO_USER="wormstein"
REPO_NAME="DGTCentaurMods"
REPO="${REPO_USER}/${REPO_NAME}"
REPO_URL="https://github.com/${REPO}"
BRANCH="auto-release"
CURRENT_VERSION=`curl -s https://raw.githubusercontent.com/${REPO}/${BRANCH}/DGTCentaurMods/DEBIAN/control | grep Version: | cut -d' ' -f2`
NEW_VERSION=`curl -s https://raw.githubusercontent.com/${REPO}/${BRANCH}/DGTCentaurMods/DEBIAN/versions | jq '.stable.latest' | tr -d \"`

RELEASE_NAME="DGTCentaurMods ${NEW_VERSION}"
RELEASE_NOTES=`cat templates/release_notes.md`

WORKSPACE="stage" ; mkdir -p $WORKSPACE

function checkForNewRelease() {
    # Check versions file fot changes
    git pull 1>/dev/null
    if [ $CURRENT_VERSION = $NEW_VERSION ]; then
        echo -e "::: No new release request"
        exit
    else
        echo -e "::: Request to build version: $NEW_VERSION\n::: Starting automated build and release"
    fi
}


function prepareGitRRepo() {
    # Update new version in tools, update control file.
    # Update control file
    cd ${BASEDIR}/../../DGTCentaurMods/DEBIAN
    sed -i "s/^Version:.*/Version: ${NEW_VERSION}/g" control
    
    # Update bootstrap files
    cd ${BASEDIR}/../../tools/bootstrap
    sed -i "s/^\$releaseVersion =.*/\$releaseVersion = \'${NEW_VERSION}\'/g" setup.ps1
    sed -i "s/^VERSION=.*/VERSION=\"${NEW_VERSION}\"/g" setup.sh

    # Update card-setup-tool
    cd ${BASEDIR}/../../tools/card-setup-tool
    sed -i "s/^\$currentReleaseVersion =.*/\$currentReleaseVersion = \'${NEW_VERSION}\'/g" DGTCentaurModsInstaller.ps1
}


function prepareAssets() {
    # Do the build, zip card-setup-tool
    cd $BASEDIR
    mkdir -p ${WORKSPACE}/assets

    # Build the release deb
    cd ${BASEDIR}/..
    ./build.sh full
    cp releases/dgtcentaurmods_${NEW_VERSION}_armhf.deb CI/${WORKSPACE}/assets
    DEB_DILE="dgtcentaurmods_${NEW_VERSION}_armhf.deb"

    # Zip the card setup tool
    cd ${BASEDIR}/../../tools/
    zip -qr ${BASEDIR}/${WORKSPACE}/assets/card-setup-tool.zip card-setup-tool
    CARD_SETUP_TOOL="card-setup-tool.zip"
}


function prepareRelease() {
    # Prepare the release  with the new version, notes and load the vars 
    cd $BASEDIR

    # Prepare notes with the new version
    awk '$1=$1' ORS='\\n' templates/release_notes.md > ${WORKSPACE}/release_notes.md
    RELEASE_NOTES=$(< ${WORKSPACE}/release_notes.md)
    RELEASE_NOTES="${RELEASE_NOTES//VERSION/$NEW_VERSION}"
    RELEASE_NOTES=$(sed 's/["]/\\&/g' <<<"$RELEASE_NOTES")
    echo -e "$RELEASE_NOTES" > ${WORKSPACE}/release_notes.md    

    # Load the default API json
    RELEASE_JSON=$(< templates/release.json)

    # Get all the info inside the JSON
    RELEASE_JSON="${RELEASE_JSON//BODY/$RELEASE_NOTES}"
    RELEASE_JSON="${RELEASE_JSON//VERSION/$NEW_VERSION}"
    RELEASE_JSON="${RELEASE_JSON//RELEASE_NAME/$RELEASE_NAME}"
    RELEASE_JSON="${RELEASE_JSON//BRANCH/$BRANCH}"
    
    # Write json for the archive
    echo "$RELEASE_JSON" > ${WORKSPACE}/release.json
}


function postRelease() {
    echo "::: Creating release at ${REPO_USER}/${REPO_NAME}"

    RESP=`curl -sX POST \
        -H "Authorization: token $GIT_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        https://api.github.com/repos/${REPO_USER}/${REPO_NAME}/releases \
        -d @stage/release.json`
    
    RELEASE_ID=`echo $RESP | jq '.id'`
    echo $RESP > ${WORKSPACE}/response.json
    echo -e "::: Created draft release for ${NEW_VERSION}. ID: ${RELEASE_ID}"
}


function postAssets() {
    for FILE in ${WORKSPACE}/assets/*; do
        NAME=`basename $FILE`
        echo -e "::: Uploading asset: $FILE as $NAME"

        RESP=`curl -sX POST \
            https://uploads.github.com/repos/${REPO_USER}/${REPO_NAME}/releases/${RELEASE_ID}/assets?name=${NAME} \
            -H "Authorization: token $GIT_TOKEN" \
            -H "Content-Type: application/octet-stream" \
            --upload-file ${FILE}`
    done
}


function publishRelease() {
    # Commit back changes to git
    git ls-files --modified ../../ | xargs git add
    git commit -m "Release ($NEW_VERSION): auto release"
    git push && \

    curl -X POST \
        -H "Authorization: token $GIT_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        https://api.github.com/repos/${REPO_USER}/${REPO_NAME}/releases/${RELEASE_ID} \
        -d '{"draft": "false"}'

}


function archive() {
    if [ ! -d archive ]; then mkdir archive; fi 
    echo "::: Archiving release"
    mv ${WORKSPACE} archive/release-${NEW_VERSION}
}


##### MAIN #####
checkForNewRelease
prepareGitRRepo
prepareAssets
prepareRelease
postRelease
postAssets
publishRelease
archive
