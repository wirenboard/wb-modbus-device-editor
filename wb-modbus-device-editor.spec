# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_all

a = Analysis(
    ['bin/wb-modbus-device-editor'],
    pathex=[],
    binaries=[],
    datas=[('wb_modbus_device_editor', 'wb_modbus_device_editor')],
    hiddenimports=["appdirs", "tkinter","pymodbus.client","json","tkinter.scrolledtext", "tkinter.filedialog", "tkinter.ttk", "serial.tools.list_ports","platform","jinja2","commentjson","requests","semantic_version","pymodbus"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='wb-modbus-device-editor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
