import os
import tkinterdnd2
from PyInstaller.utils.hooks import collect_all

TKDND_PATH = os.path.dirname(tkinterdnd2.__file__)

# Collect all TkinterDnD2 files
tkdnd_datas, tkdnd_binaries, tkdnd_hiddenimports = collect_all('tkinterdnd2')

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[
        (os.path.join(TKDND_PATH, 'tkdnd'), 'tkdnd'),
        *tkdnd_binaries,
    ],
    datas=[
        (os.path.join(TKDND_PATH, 'tkdnd'), 'tkdnd'),
        *tkdnd_datas,
    ],
    hiddenimports=[
        'tkinterdnd2',
        *tkdnd_hiddenimports,
    ],
    hookspath=['hooks'],
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
    name='Simplified PIDs Viz',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)