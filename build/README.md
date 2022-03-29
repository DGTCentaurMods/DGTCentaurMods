# Build tool
This will build a deb package out of the cloned branch. It means that not all the time the tool will get you a working build of the software. This tool is meant to be used mainly by the developers. Usually, if try to build the `master` branch, you should get a working build though.

## How to use the tool?
- To start a new build process just run: `./build.sh`. This runs as interactive mode.
- To start a headless build process run: `./build.sh full`. This will perform all operations without interaction.
- Although performed at the start, cleaning can be done by `./build.sh clean`

Resulting build file will be in `build/releases/`.
