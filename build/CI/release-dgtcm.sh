#!/usr/bin/bash

#GIT_TOKEN=Set it in .ci.conf
#DISCORD_WH=Set it in .ci.conf

    if [ -e .ci.conf ]; then source .ci.conf
    else echo "No .ci.conf file"; exit 1; fi

BASEDIR=`pwd`

REPO_USER="EdNekebno"
REPO_NAME="DGTCentaurMods"
REPO="${REPO_USER}/${REPO_NAME}"
REPO_URL="https://github.com/${REPO}"
BRANCH="master"
VERSIONS_FILE="../../DGTCentaurMods/DEBIAN/versions"
CURRENT_VERSION=`cat ../../${REPO_NAME}/DEBIAN/versions | jq -r '.stable | .["release"]' | tr -d \"`
NEW_VERSION=`curl -s https://raw.githubusercontent.com/${REPO}/${BRANCH}/DGTCentaurMods/DEBIAN/versions | jq '.stable.release' | tr -d \"`

CURR_PRE_RELEASE=`cat ../../${REPO_NAME}/DEBIAN/versions | jq -r '.stable | .["pre-release"]' | tr -d \"`
NEW_PRE_RELEASE=`curl -s https://raw.githubusercontent.com/${REPO}/${BRANCH}/DGTCentaurMods/DEBIAN/versions | jq -r '.stable | .["pre-release"]' | tr -d \"`

WORKSPACE="stage" ; mkdir -p $WORKSPACE

function status() {
    echo -e "\
RELEASE:
Current version: $CURRENT_VERSION
Requested new version: $NEW_VERSION
PRE-RELEAsE:
Current pre-release: $CURR_PRE_RELEASE
Requested pre-release: $NEW_PRE_RELEASE"
}

function sayOnDiscord() {
    MSG="$1"
    TIMESTAMP=`date +%H:%M:%S`
    JSON=$(cat <<-END
    {
        "username": "DGTCM CI",
        "content": "\`\`\`[$TIMESTAMP] $MSG\`\`\`"
    }
END
)
    curl \
        -H "Content-Type: application/json" \
        -d "$JSON" \
        $DISCORD_WH
}


function checkForNewRelease() {
    # Check versions file fot changes
    # If pre-release match a latest release, exit
    if [ $CURRENT_VERSION = $NEW_PRE_RELEASE ]; then echo -e "::: Latest version should never match a pre-release or opposite. Aborting"; exit 1; fi
    if [ $CURRENT_VERSION = $NEW_VERSION ]; then
        echo -e "::: No new release request"
    else
        IS_PRERELEASE=0
        RELEASE_NAME="DGTCentaurMods ${NEW_VERSION}"
        COMMIT_MSG="Release: DGTCentaurMods ${NEW_VERSION}"
        sayOnDiscord "::: Request to build $COMMIT_MSG at $REPO"
        echo -e "::: Request to build version: $NEW_VERSION\n::: Starting automated build and release"
        return
    fi

    if [ $CURR_PRE_RELEASE = $NEW_PRE_RELEASE ]; then
        echo -e "::: No new pre-release request"
        exit
    else
        IS_PRERELEASE=1
        NEW_VERSION="$NEW_PRE_RELEASE"
        RELEASE_NAME="DGTCentaurMods ${NEW_VERSION} - Pre-release"
        COMMIT_MSG="Pre-release: DGTCentaurMods ${NEW_VERSION}"
        sayOnDiscord "::: Request to build pre-release $COMMIT_MSG at $REPO"
        echo -e "::: Request to build pre-release version: $NEW_VERSION\n::: Starting automated build"
        #return
    fi
}


function prepareGitRRepo() {
    # Update new version in tools, update control file.
    # Update control file
    cd ${BASEDIR}/../../DGTCentaurMods/DEBIAN
    git pull

    if [ ! $IS_PRERELEASE = 1 ]; then 
        sed -i "s/^Version:.*/Version: ${NEW_VERSION}/g" control

        # Update bootstrap files
        cd ${BASEDIR}/../../tools/bootstrap
        sed -i "s/^\$currentReleaseVersion =.*/\$currentReleaseVersion = \'${NEW_VERSION}\'/g" setup.ps1
        sed -i "s/^VERSION=.*/VERSION=\"${NEW_VERSION}\"/g" setup.sh

        # Update card-setup-tool
        cd ${BASEDIR}/../../tools/card-setup-tool
        sed -i "s/^\$currentReleaseVersion =.*/\$currentReleaseVersion = \'${NEW_VERSION}\'/g" DGTCentaurModsInstaller.ps1
    else
        # Update control file
        sed -i "s/^Version:.*/Version: ${NEW_VERSION}/g" control
        #OUT=`jq '.stable["release"] = "'"$NEW_VERSION"'"' $VERSIONS_FILE` ; echo "$OUT" > $VERSIONS_FILE
    fi
}


function prepareAssets() {
    sayOnDiscord "::: Preparing build assets"
    # Do the build, zip card-setup-tool
    cd $BASEDIR
    mkdir -p ${WORKSPACE}/assets

    # Build the release deb
    cd ${BASEDIR}/..
    ./build.sh full
    cp releases/* CI/${WORKSPACE}/assets
    sayOnDiscord "::: dgtcentaurmods_${NEW_VERSION}_armhf.deb prepared"

    # Zip the card setup tool
    cd ${BASEDIR}/../../tools/
    zip -qr ${BASEDIR}/${WORKSPACE}/assets/card-setup-tool_${NEW_VERSION}.zip card-setup-tool
    sayOnDiscord "::: card-setup-tool_${NEW_VERSION}.zip prepared"
}


function prepareRelease() {
    # Prepare the release  with the new version, notes and load the vars 
    cd $BASEDIR

    # Prepare notes with the new version
    if [ ! $IS_PRERELEASE = 1 ]; then
        awk '$1=$1' ORS='\\n' templates/release_notes.md > ${WORKSPACE}/release_notes.md
    else
        awk '$1=$1' ORS='\\n'  templates/pre_release_notes.md > ${WORKSPACE}/release_notes.md
    fi

    RELEASE_NOTES=$(< ${WORKSPACE}/release_notes.md)
    RELEASE_NOTES="${RELEASE_NOTES//VERSION/$NEW_VERSION}"
    RELEASE_NOTES=$(sed 's/["]/\\&/g' <<<"$RELEASE_NOTES")
    echo -e "$RELEASE_NOTES" > ${WORKSPACE}/release_notes.md    

    # Load the default API json
    RELEASE_JSON=$(< templates/release.json)

    # Get all the info inside the JSON
    if [ $IS_PRERELEASE = 1 ]; then
        RELEASE_JSON="${RELEASE_JSON//PRE_RELEASE/true}"
    else
        RELEASE_JSON="${RELEASE_JSON//PRE_RELEASE/false}"
    fi

    RELEASE_JSON="${RELEASE_JSON//VERSION/$NEW_VERSION}"
    RELEASE_JSON="${RELEASE_JSON//BODY/$RELEASE_NOTES}"
    RELEASE_JSON="${RELEASE_JSON//RELEASE_NAME/$RELEASE_NAME}"
    RELEASE_JSON="${RELEASE_JSON//BRANCH/$BRANCH}"

    # Write json for the archive
    echo "$RELEASE_JSON" > ${WORKSPACE}/release.json

    sayOnDiscord "::: Release json request prepared"
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
    sayOnDiscord "::: Created draft release. ID: ${RELEASE_ID}"
}


function postAssets() {
    for FILE in ${WORKSPACE}/assets/*; do
        NAME=`basename $FILE`
        echo -e "::: Uploading asset: $FILE as $NAME"
        sayOnDiscord "::: Uploading assets: $NAME"

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
    git commit -m "$COMMIT_MSG"
    git push && \

    PUBLISH=`curl -X POST \
        -H "Authorization: token $GIT_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        https://api.github.com/repos/${REPO_USER}/${REPO_NAME}/releases/${RELEASE_ID} \
        -d '{"draft": "false"}'`
    
    echo "$PUBLISH" > ${WORKSPACE}/publish.json
    sayOnDiscord "::: Release published and archived.\nEnjoy your day!"
}


function archive() {
    if [ ! -d archive ]; then mkdir archive; fi 
    echo "::: Archiving release"
    mv ${WORKSPACE} archive/release-${NEW_VERSION}
}


##### MAIN #####
status
checkForNewRelease
prepareGitRRepo
prepareAssets
prepareRelease
postRelease
postAssets
publishRelease
archive
