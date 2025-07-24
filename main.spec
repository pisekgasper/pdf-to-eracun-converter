# -*- mode: python ; coding: utf-8 -*-

import sys
import os
import glob
from PyInstaller.utils.hooks import copy_metadata

# Collect metadata for required packages
datas = copy_metadata('readchar') + copy_metadata('inquirer')

# Add ZBar DLLs for Windows
binaries = []
if sys.platform == 'win32':
    # ZBar installation path
    zbar_path = r'C:\Program Files (x86)\ZBar\bin'
    
    if os.path.exists(zbar_path):
        # Find all DLL files in the ZBar bin directory
        dll_pattern = os.path.join(zbar_path, '*.dll')
        dll_files = glob.glob(dll_pattern)
        
        if dll_files:
            print(f"\nFound {len(dll_files)} DLL files in {zbar_path}:")
            for dll in dll_files:
                binaries.append((dll, '.'))
                print(f"  - Adding: {os.path.basename(dll)}")
        else:
            print(f"\nWARNING: No DLL files found in {zbar_path}")
    else:
        print(f"\nERROR: ZBar directory not found at {zbar_path}")
        print("Please ensure ZBar is installed or update the path in main.spec")
        
    # Also try to find pyzbar's bundled DLLs if they exist
    try:
        import pyzbar
        pyzbar_path = os.path.dirname(pyzbar.__file__)
        pyzbar_dll_pattern = os.path.join(pyzbar_path, '*.dll')
        pyzbar_dlls = glob.glob(pyzbar_dll_pattern)
        
        if pyzbar_dlls:
            print(f"\nFound {len(pyzbar_dlls)} pyzbar bundled DLLs:")
            for dll in pyzbar_dlls:
                binaries.append((dll, '.'))
                print(f"  - Adding: {os.path.basename(dll)}")
    except Exception as e:
        print(f"\nCould not check for pyzbar bundled DLLs: {e}")

if not binaries and sys.platform == 'win32':
    print("\n" + "="*60)
    print("WARNING: No DLLs were found to bundle!")
    print("The executable will likely fail with missing DLL errors.")
    print("Make sure ZBar is installed at: C:\\Program Files (x86)\\ZBar\\bin")
    print("="*60 + "\n")

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