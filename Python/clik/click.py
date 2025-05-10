import pyautogui
import time
delay = 0.05
hold = 0.02
try:
    print("starting")
    while True:
        for key in ['w','s','a','d']:
         pyautogui.press(key)
         time.sleep(delay)
except KeyboardInterrupt:
    print("stopped")
