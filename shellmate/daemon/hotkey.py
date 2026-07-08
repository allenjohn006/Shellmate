from pynput import keyboard
from shellmate.tui.popup import run_popup
import threading
import time
import sys

def on_activate():
    # To prevent multiple instances from stacking up
    t = threading.Thread(target=run_popup)
    t.daemon = True
    t.start()
    
def start():
    print("Shellmate Hotkey Daemon Started. Listening for <ctrl>+<backslash>...")
    
    # Define the hotkey — changed from <ctrl>+<space> to <ctrl>+<backslash>
    # to avoid conflict with VS Code's IntelliSense shortcut.
    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse('<ctrl>+<backslash>'),
        on_activate
    )

    def for_canonical(f):
        return lambda k: f(listener.canonical(k))

    listener = keyboard.Listener(
        on_press=for_canonical(hotkey.press),
        on_release=for_canonical(hotkey.release)
    )
    
    listener.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    start()
