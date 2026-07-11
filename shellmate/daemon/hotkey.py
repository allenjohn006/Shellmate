import threading
import time
import sys

def on_activate():
    """Spawn the TUI popup in a daemon thread."""
    from shellmate.tui.popup import run_popup
    t = threading.Thread(target=run_popup)
    t.daemon = True
    t.start()

def start():
    """
    Entry point for shellmate-daemon.
    Listens globally for Ctrl+\\ to open the TUI popup.

    WSL NOTE: pynput global keyboard hooking requires an X server.
    In WSL2, this means you need WSLg (Windows 11) or a manual X server
    (e.g. VcXsrv on Windows 10).

    If no display is available, the daemon falls back to a simple
    interactive mode where pressing Enter in the terminal opens the TUI.
    """
    try:
        from pynput import keyboard

        print("Shellmate Hotkey Daemon Started. Listening for <ctrl>+<backslash>...")
        print("Press Ctrl+\\ anywhere to open the Shellmate TUI.")

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

    except Exception as e:
        # Graceful fallback for headless WSL2 without a display server
        print(f"[shellmate-daemon] Could not start global hotkey listener: {e}")
        print("[shellmate-daemon] Falling back to terminal mode.")
        print("[shellmate-daemon] Press ENTER to open the TUI popup. Ctrl+C to quit.")
        try:
            while True:
                user_input = input()
                if user_input.strip() == "" or user_input.strip().lower() in ("open", "sm", "shellmate"):
                    on_activate()
        except (KeyboardInterrupt, EOFError):
            sys.exit(0)

if __name__ == "__main__":
    start()
