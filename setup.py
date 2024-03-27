#!/usr/bin/env python

from setuptools import setup


def get_version():
    with open("debian/changelog", "r", encoding="utf-8") as f:
        return f.readline().split()[1][1:-1]


setup(
    name="wb-modbus-device-editor",
    version=get_version(),
    author="Ekaterina Volkova",
    author_email="ekaterina.volkova@wirenboard.ru",
    maintainer="Wiren Board Team",
    maintainer_email="info@wirenboard.com",
    description="Wiren Board modbus device editor",
    url="https://github.com/wirenboard/py-modbus-device-editor",
    packages=["wb_modbus_device_editor"],
    install_requires=["pymodbus", "pyserial","jinja2","commentjson","requests"],
    license="MIT",
)
