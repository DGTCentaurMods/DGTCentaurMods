#!/usr/bin/bash

GIT_USER="wormstein"
#GIT_TOKEN=Create a .git_passwd file with this variable
if [ -e .git_token ]; then source .git_token 
else echo "No .git_token file"; exit 1; fi

BASEDIR=`pwd`

REPO_NAME="DGTCentaurMods"
REPO="${GIT_USER}/${REPO_NAME}"
REPO_URL="https://github.com/${REPO}"
BRANCH="auto-release"
CURRENT_VERSION=`curl -s https://raw.githubusercontent.com/${REPO}/${BRANCH}/DGTCentaurMods/DEBIAN/control | grep Version: | cut -d' ' -f2`
#NEW_VERSION=`curl -s https://raw.githubusercontent.com/${REPO}/${BRANCH}/DGTCentaurMods/DEBIAN/versions | jq '.stable.latest' | tr -d \"`
NEW_VERSION='1.1.3'

RELEASE_NAME="DGTCentaurMods ${NEW_VERSION}"
RELEASE_NOTES=`cat templates/release_notes_new.md`

WORKSPACE="stage" ; mkdir -p $WORKSPACE
#WORKSPACE="release-${NEW_VERSION}"

function checkForNewRelease() {
    # Check versions file fot changes
    git pull
    if [ $CURRENT_VERSION = $NEW_VERSION ]; then
        return
    else
        echo -e "::: No need for a release"
        exit 1
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
    zip -r ${BASEDIR}/${WORKSPACE}/assets/card-setup-tool.zip card-setup-tool
    CARD_SETUP_TOOL="card-setup-tool.zip"
}


function prepareRelease() {
    # Prepare the release  with the new version, notes and load the vars
    
    cd $BASEDIR

    # Prepare notes
    RELEASE_NOTES=$(< templates/release_notes.md)
    RELEASE_NOTES="${RELEASE_NOTES//VERSION/$NEW_VERSIOPN}"

    # Prepare the API json
    RELEASE_JSON=$(< templates/release.json)
    BODY=$(< templates/release_notes.md)
    
    RELEASE_JSON="${RELEASE_JSON//BODY/$BODY}"
    RELEASE_JSON="${RELEASE_JSON//VERSION/$NEW_VERSION}"
    RELEASE_JSON="${RELEASE_JSON//RELEASE_NAME/$RELEASE_NAME}"
    RELEASE_JSON="${RELEASE_JSON//BRANCH/$BRANCH}"
    
    echo "$RELEASE_JSON" > ${WORKSPACE}/release.json
    echo "RELEASE_NOTES" > ${WORKSPACE}/release_notes.md

    echo $RELEASE_JSON
}


function postRelease() {
    RESP=`curl -s --user "$GIT_USER:$GIT_TOKEN" -X POST \
        https://api.github.com/repos/${GIT_USER}/${REPO_NAME}/releases \ 
        -d "${REL}"`

    RELEASE_ID=`echo $RESP | jq '.[].id'`
    echo $RESP
    echo -e "::: Created new draft release for ${NEW_VERSION}. ID: ${RELEASE_ID}"
}


function postAssets() {
    curl -s \
        --user "$GIT_USER:$GIT_TOKEN" \
        -X POST \
        https://uploads.github.com/repos/${GIT_USER}/${REPO_NAME}/releases/${RELEASE_ID}/assets?name=${DEB_FILE} \
        --header 'Content-Type: application/octet-stream' \
        --upload-file ${WORKSPACE}/${DEB_FILE}
}


function publishRelease() {
    :
}
echo $1
$1

#function start() {
#mkdir ${WORKSPACE} ££ cd ${WORKSPACE}
#cloneRepo

#cd $REPO_NAME


##### MAIN #####
#if [ $CURRENT_VERSION = $NEW_VERSION ]; then
#    start
#else
#    exit 1



# 1. Clone the repo
# 2. Check version file with git diff for the new version
#       NO: exit 0

# 3. YES: do the changes in the repo with the new versions: card-tool,
# bootstrap, control file.
# 4. Prepare the assets: build the .deb file, zip card-setup-tool
# 5. Prepare the release notes variable
# 5. Commit and push the repo changes
# 6. publish the release

# Any step: NO: exit 0
