#!/bin/bash

BUILD_DIR=build
DIST_DIR=dist
VENV_DIR=.venv_docker

linux() {
	python3 -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate
	pip install -r requirements.txt
	pyinstaller --distpath $DIST_DIR/linux ./wb-modbus-device-editor.spec
}

windows() {
	wine pip install -r requirements.txt
	wine pyinstaller --distpath $DIST_DIR/windows ./wb-modbus-device-editor.spec
	chmod -R 755 $DIST_DIR
	ls -l $DIST_DIR
}

clean() {
	rm -rf $BUILD_DIR
	rm -rf $DIST_DIR
	rm -rf $VENV_DIR
}

"$@"