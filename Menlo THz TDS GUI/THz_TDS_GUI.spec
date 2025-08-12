# THz_TDS_GUI.spec

# PyInstaller spec file for THz_TDS_GUI
# Build with: pyinstaller THz_TDS_GUI.spec

block_cipher = None

from PyInstaller.utils.hooks import collect_submodules

# Import any hidden modules your code uses
hidden_imports = collect_submodules('plots') + collect_submodules('processing')

a = Analysis(
    ['THz_TDS_GUI.py'],  # Entry point
    pathex=[],
    binaries=[],
    datas=[
        ('res/THzTDS_icon.ico', 'res'),
        ('res/*.svg', 'res')
    ],
    hiddenimports=hidden_imports,
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
    name='THz TDS GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # True = show console, False = GUI only
    icon='res/THzTDS_icon.ico',
    onefile=True  # <- bundle everything into a single .exe
)
