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


sys.path = sys.path[-3:]

print(sys.path)

sitepackages = Path.absolute(Path(sysconfig.get_paths()["purelib"]))

sitepackages_list = get_sitepackages(sitepackages)

shiny = sitepackages / "shiny"
# shinyswatch = sitepackages / "shinyswatch"
# yamldataclassconfig = sitepackages / "yamldataclassconfig"
# dataclasses_json = sitepackages / "dataclasses_json"
# marshmallow = sitepackages / "marshmallow"
langchain = sitepackages / "langchain"
# typing_inspect = sitepackages / "typing_inspect.py"
# mypy_extensions = sitepackages / "mypy_extensions.py"
# marshmallow_enum = sitepackages / "marshmallow_enum"
www = os.path.abspath("www")
data = os.path.abspath("data")

data_files = [
    ("app.py", "."),
    ("validators.py", "."),
    ("utils.py", "."),
    ("settings.yaml", "."),
    ("resources_paths.py", "."),
    ("prompts.py", "."),
    ("pages.py", "."),
    ("LICENSE.md", "."),
    ("classes.py", "."),
    ("__init__.py", "."),
    (data, "data"),
    (www, "www"),
    # (langchain, "./langchain"),
    # (shiny, "./shiny"),
]

datas = data_files + sitepackages_list


# print(datas)

a = Analysis(
    ["story_generator.py"],
    pathex=[sitepackages],
    binaries=[],
    datas=datas,
    # datas=[
    #     ("app.py", "."),
    #     ("validators.py", "."),
    #     ("utils.py", "."),
    #     ("settings.yaml", "."),
    #     ("resources_paths.py", "."),
    #     ("prompts.py", "."),
    #     ("pages.py", "."),
    #     ("LICENSE.md", "."),
    #     ("classes.py", "."),
    #     ("__init__.py", "."),
    #     ("data", "data"),
    #     ("www", "www"),
    #     # (sitepackages, "site-packages"),
    #     (langchain, "./langchain"),
    #     (shiny, "./shiny"),
    #     (shinyswatch, "./shinyswatch"),
    #     (yamldataclassconfig, "./yamldataclassconfig"),
    #     (dataclasses_json, "./dataclasses_json"),
    #     (marshmallow, "./marshmallow"),
    #     (typing_inspect, "."),
    #     (mypy_extensions, "."),
    #     (marshmallow_enum, "./marshmallow_enum"),
    # ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="story_generator",
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
