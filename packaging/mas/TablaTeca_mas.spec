# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller para la edición Mac App Store de TablaTeca.
# Se ejecuta desde la raíz del repositorio:
#   python -m PyInstaller packaging/mas/TablaTeca_mas.spec --clean --noconfirm \
#       --distpath dist-mas --workpath build-mas
# La firma NO se hace aquí: la hace packaging/mas/sign_and_package.sh.
import os

ROOT = os.path.abspath(os.getcwd())
MARKETING_VERSION = os.environ.get("MAS_MARKETING_VERSION", "1.0")
BUILD_NUMBER = os.environ.get("MAS_BUILD_NUMBER", "1")

block_cipher = None

a = Analysis(
    [os.path.join(ROOT, "launcher_native_websockets.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, "app"), "app"),
        (os.path.join(ROOT, "config.py"), "."),
        (os.path.join(ROOT, "wsgi.py"), "."),
        (os.path.join(ROOT, ".env"), "."),
        (os.path.join(ROOT, "VERSION"), "."),
        (os.path.join(ROOT, "requirements.txt"), "."),
    ],
    hiddenimports=[
        "flask", "flask_login", "flask_session", "pymongo", "requests",
        "webview", "werkzeug", "jinja2", "markupsafe", "itsdangerous",
        "click", "blinker", "boto3", "botocore", "s3transfer",
        "jmespath", "python_dateutil", "urllib3", "certifi",
        "charset_normalizer", "idna", "six", "websockets",
        "asyncio", "threading", "tempfile", "pathlib", "datetime",
        "json", "os", "sys", "time",
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
    [],
    exclude_binaries=True,
    name="TablaTeca",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX invalida firmas y la revisión de la tienda
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="TablaTeca",
)

app = BUNDLE(
    coll,
    name="TablaTeca.app",
    icon=os.path.join(ROOT, "edf_developer.icns"),
    bundle_identifier="com.edefrutos.tablateca",
    info_plist={
        "CFBundleName": "TablaTeca",
        "CFBundleDisplayName": "TablaTeca",
        # La tienda exige que CFBundleVersion aumente en cada subida
        "CFBundleVersion": BUILD_NUMBER,
        "CFBundleShortVersionString": MARKETING_VERSION,
        "CFBundleExecutable": "TablaTeca",
        "CFBundlePackageType": "APPL",
        "CFBundleSignature": "????",
        "LSMinimumSystemVersion": "12.0",  # arm64 solo: Apple exige >= 12.0 sin x86_64
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": False,
        "LSApplicationCategoryType": "public.app-category.productivity",
        "CFBundleDevelopmentRegion": "es",
        "CFBundleLocalizations": ["es", "en"],
        "NSHumanReadableCopyright": "Copyright © 2026 Eugenio de Frutos Sanchez",
    },
)
