# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import copy_metadata

# Collect metadata for required packages
datas = copy_metadata('readchar') + copy_metadata('inquirer')

# Add ZBar DLLs for Windows
binaries = []
if sys.platform == 'win32':
    # Try to find ZBar installation
    possible_paths = [
        r'C:\ProgramData\chocolatey\lib\zbar\tools',
        r'C:\tools\zbar\bin',
        r'C:\Program Files\ZBar\bin',
        r'C:\Program Files (x86)\ZBar\bin'
    ]
    
    zbar_found = False
    for path in possible_paths:
        if os.path.exists(path):
            # Include all DLLs from ZBar directory
            binaries += [(os.path.join(path, '*.dll'), '.')]
            zbar_found = True
            print(f"Found ZBar at: {path}")
            break
    
    if not zbar_found:
        print("WARNING: ZBar DLLs not found. The executable may not work properly.")
        print("Please ensure ZBar is installed via: choco install zbar")

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,  # Include the ZBar DLLs
    datas=datas,
    hiddenimports=[
        'pyzbar', 
        'pyzbar.pyzbar', 
        'importlib.metadata',
        'readchar',
        'inquirer.render.console'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='pdf-to-eslog',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)