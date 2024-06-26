# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

a = Analysis(
    ["bin/wb-modbus-device-editor"],
    pathex=[],
    binaries=[],
    datas=[("wb_modbus_device_editor", "wb_modbus_device_editor")],
    hiddenimports=[
        "appdirs",
        "tkinter",
        "pymodbus.client",
        "json",
        "tkinter.scrolledtext",
        "tkinter.filedialog",
        "tkinter.ttk",
        "serial.tools.list_ports",
        "platform",
        "jinja2",
        "commentjson",
        "requests",
        "pymodbus",
        "semantic_version"
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="wb-modbus-device-editor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="wb-modbus-device-editor",
)
