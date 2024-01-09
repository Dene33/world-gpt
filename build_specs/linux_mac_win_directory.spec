# -*- mode: python ; coding: utf-8 -*-


block_cipher = None
import os
from pathlib import Path
import sys
import sysconfig

def get_sitepackages(sitepackages: Path):
    datas = []
    for item in sitepackages.iterdir():
        if item.is_dir() and not item.name.endswith("-info"):
            folder_path = str(item.absolute())
            folder_name = item.name
            datas.append((folder_path, f"./{folder_name}"))

        if item.is_file() and item.suffix == ".py":
            file_path = str(item.absolute())
            datas.append((file_path, "."))

    return datas

sitepackages = Path.absolute(Path(sysconfig.get_paths()["purelib"]))

sitepackages_list = get_sitepackages(sitepackages)

shiny = sitepackages / "shiny"
langchain = sitepackages / "langchain"
www = os.path.abspath("www")
data = os.path.abspath("data")
ui_modules = os.path.abspath("ui_modules")

data_files = [
    ("../app.py", "."),
    ("../validators.py", "."),
    ("../utils.py", "."),
    ("../settings.yaml", "."),
    ("../resources_paths.py", "."),
    ("../prompts.py", "."),
    ("../pages.py", "."),
    ("../LICENSE.md", "."),
    ("../classes.py", "."),
    ("../__init__.py", "."),
    (data, "./data"),
    (www, "./www"),
    (ui_modules, "./ui_modules"),
]

datas = data_files + sitepackages_list


a = Analysis(
    ["../story_generator.py"],
    pathex=[sitepackages],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "shiny",
        "shinyswatch",
        "yamldataclassconfig",
        "dataclasses_json",
        "marshmallow",
        "strenum",
        "openai",
        "prompt_toolkit",
        "langchain",
        "shinyswatch",
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
    name="story_generator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    upx=True,
    upx_exclude=[],
    name="story_generator",
)
