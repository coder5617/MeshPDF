# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        'fitz',  # PyMuPDF
        'PIL',
        'PIL.Image',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
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
    name='MeshPDF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)