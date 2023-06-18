import os
import sys
from shiny._main import main
import platform

path = os.path.dirname(os.path.abspath(__file__))
apath = os.path.join(path, "app.py")

if platform.system() == "Windows":
    drive, apath = os.path.splitdrive(apath)
    apath = apath.replace("\\", "/")

sys.argv = [
    "shiny",
    "run",
    "--launch-browser",
    "--port",
    "37955",
    apath,
]
main()
