# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# Gom toàn bộ tài nguyên, metadata và file tĩnh của streamlit
datas, binaries, hiddenimports = collect_all('streamlit')

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=binaries,
    datas=datas + [('app.py', '.')], # Đảm bảo file app.py của bạn được nhúng vào cùng
    hiddenimports=hiddenimports + ['streamlit', 'pandas', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='XocDiaTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Ẩn bảng đen console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)