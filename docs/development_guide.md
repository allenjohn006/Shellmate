# Development & Deployment Guide

This guide provides steps for setting up, running, testing, and debugging Shellmate within a Linux/WSL development environment.

## Initial Setup for Development

### 1. Configure the Environment
Ensure Python 3.8+ is installed on your Linux / WSL instance. Check your Python version:
```bash
python3 --version
```

Make sure clipboard utilities are installed:
- On native Linux (Ubuntu):
  ```bash
  sudo apt-get update
  sudo apt-get install -y xclip
  ```
- On WSL: WSL interacts natively with the Windows clipboard, but `xclip` or standard configurations should be available if you are running GUI environments inside WSL.

### 2. Git Clone and Install
Clone the repository and install it in "editable" development mode. This registers the console entrypoints (`shellmate` and `shellmate-daemon`) while letting you see changes immediately without reinstalling:
```bash
git clone https://github.com/allenjohn006/Shellmate.git
cd Shellmate
pip install -e .
```

Verify that the CLI works:
```bash
shellmate --help
```

### 3. Run the Onboarding Setup Wizard
Run the initialization CLI flow:
```bash
shellmate setup
```
Provide your details (name, preferred shell, favorite editor, and your API keys). This creates:
- Configuration home directory: `~/.shellmate/`
- Configuration file: `~/.shellmate/config.yaml`
- Subdirectories: `~/.shellmate/projects/`
- Aliases: Adds `alias sm="shellmate"` and starts `shellmate-daemon &` inside your `.bashrc` or `.zshrc`.

---

## Working with the Hotkey Daemon

The hotkey daemon listens for `Ctrl+Space` globally. 

### 1. Launching/Restarting the Daemon
The daemon runs as a background process. If you change the daemon script or want to restart it:
```bash
# Terminate existing daemon instances
pkill -f shellmate-daemon

# Start the daemon in the background
shellmate-daemon &
```

### 2. Testing the TUI Independently
You can bypass the daemon entirely to test the TUI layout and chat interface directly:
```bash
shellmate __popup
```
*(This hidden CLI entrypoint directly launches the textual app in the current active terminal, allowing you to view and debug TUI layout styling errors.)*

---

## Troubleshooting & Debugging

### API Connection Issues
If you hit connections limits or get authentication failures:
- Check your config values with:
  ```bash
  shellmate config list
  ```
- Re-verify your keys or update them directly:
  ```bash
  shellmate config set api_key "sk-or-your-key"
  ```

### Pynput and Keyboard Listener Failures
- The `pynput` module relies on a display server (like X11) to capture keyboard hooks globally on Linux.
- If you are running in a headless WSL terminal without GUI system routing configured, `pynput` may fail to start.
- Ensure your WSL has GUI routing configured or test the daemon under environment instances with a valid `$DISPLAY` export set (e.g. `export DISPLAY=:0`).
- If you get an import or display error from `pynput`, ensure X Server (like VcXsrv or native WSLG on Windows 11) is active.
