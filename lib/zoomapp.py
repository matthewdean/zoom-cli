import os
import psutil
import subprocess
import platform

def start():
    if platform.system() == "Darwin":
        app_path = "/Applications/zoom.us.app"
        subprocess.Popen(['/usr/bin/open', "-j", "-a", app_path])
    elif platform.system() == "Windows":
        app_path = os.path.expandvars("%APPDATA%/Zoom/bin/Zoom.exe")
        subprocess.Popen([app_path], creationflags=subprocess.DETACHED_PROCESS)

def stop():
    for proc in psutil.process_iter():
        if proc.name() in ["zoom.us", "Zoom.exe"]:
            proc.terminate()
            proc.wait()

def restart():
    stop()
    start()