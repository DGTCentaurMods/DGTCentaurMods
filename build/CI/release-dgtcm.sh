#!/usr/bin/bash

GIT_USER="wormstein"
#GIT_TOKEN=Create a .git_passwd file with this variable
if [ -e .git_token ]; then source .git_token 
else echo "No .git_token file"; exit 1; fi

BASEDIR=`pwd`

REPO_NAME="DGTCentaurMods"
REPO="${GIT_USER}/${REPO_NAME}"
REPO_URL="https://github.com/${REPO}"
BRANCH="update-tst"
CURRENT_VERSION=`curl -s https://raw.githubusercontent.com/${REPO}/${BRANCH}/DGTCentaurMods/DEBIAN/control | grep Version: | cut -d' ' -f2`
#NEW_VERSION=`curl -s https://raw.githubusercontent.com/${REPO}/${BRANCH}/DGTCentaurMods/DEBIAN/versions | jq '.stable.latest' | tr -d \"`
NEW_VERSION='1.1.3'

RELEASE_NAME="DGTCentaurMods ${NEW_VERSION}"
RELEASE_NOTES=`cat templates/release_notes.md`

WORKSPACE="release-${NEW_VERSION}"

function checkForRelease() {
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

    # Zip the card setup tool
    cd ${BASEDIR}/../../tools/
    zip -r ${BASEDIR}/${WORKSPACE}/assets/card-setup-tool.zip card-setup-tool
}


function prepareReleaseNotes() {
    # Update release notes with the new version
    cd $BASEDIR
    sed 's/NEW_VERSION/${NEW_VERSION}/g' release_notes.md > ${BASEDIR}/${WORKSPACE}/release_notes.md
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
