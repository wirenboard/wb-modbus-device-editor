#!/usr/bin/env bash

BUILD_DIR=build
DIST_DIR=dist
VENV_DIR=.venv_docker

linux() {
	pip install pyinstaller
	pip install -r requirements.txt
	pyinstaller --distpath $DIST_DIR/linux ./linux.spec
}

windows() {
	wine pip install -r requirements.txt
	wine pyinstaller --distpath $DIST_DIR/windows ./windows.spec
}

clean() {
	rm -rf $BUILD_DIR
	rm -rf $DIST_DIR
	rm -rf $VENV_DIR
}

"$@"