import time
import subprocess
import pyautogui
from pathlib import Path

TORCS_DIR = Path(__file__).parent.parent / 'torcs'

def launch_torcs(vision):
    "Kill and launch TORCS with automatic race start"
    close_torcs()
    time.sleep(1)
    if vision is True:
        subprocess.Popen(['wtorcs','-nofuel','-nodamage','-nodamage','-vision','&'], cwd=TORCS_DIR, shell=True)
    else:
        subprocess.Popen(['wtorcs','-nofuel','-nodamage','-nodamage','&'], cwd=TORCS_DIR, shell=True)
    time.sleep(10)
    pyautogui.press("enter", presses=3)
    time.sleep(5)

def close_torcs():
    subprocess.call("taskkill /f /im wtorcs.exe")
        
if __name__ == "__main__":
    launch_torcs(False)