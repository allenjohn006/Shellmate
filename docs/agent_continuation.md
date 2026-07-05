# Agent Continuation & Memory Guide

This document contains context, state variables, and architectural instructions for any developer agent resuming work on Shellmate inside the Ubuntu/WSL environment.

---

## 🎯 Current Context & Project State

The core codebase has been successfully implemented on Windows and pushed to the GitHub repository:
- **Repository**: `https://github.com/allenjohn006/Shellmate.git`
- **Branch**: `main`

The next phase of work takes place inside your **Ubuntu/WSL** instance (using the VS Code WSL remote extension).

---

## 🛠️ Instructions for Continuation (For the AI Agent in WSL)

When you resume execution inside VS Code connected to Ubuntu/WSL, follow these steps to continue development:

### 1. Pull changes
Verify that the files have been updated inside your Linux workspace:
```bash
git pull origin main
```

### 2. Install Development Dependencies
Install dependencies locally into the active environment:
```bash
pip install -e .
```
*(This installs PyYAML, Typer, Rich, Textual, Requests, Pyperclip, and Pynput.)*

### 3. Verify Configuration Wizard
Ensure that the wizard can write files and correctly append lines to your shell RC profile:
```bash
shellmate setup
```
Validate that:
- `~/.shellmate/config.yaml` is generated correctly.
- Shell profile entries (`~/.bashrc` or `~/.zshrc`) are written only once.

### 4. Running the Tests
To verify all integrations:
- **Inline Assistant**: `shellmate "display directories sorting by size"`
- **Error Explainer**: `shellmate explain "bash: sm: command not found"`
- **Agent Mode**: `shellmate agent "list all files in the current folder, select the largest file, and print its name"`
- **TUI Popup (Manual UI trigger)**: `shellmate __popup`
- **Hotkey Daemon**: Run `shellmate-daemon &` and verify if pressing `Ctrl+Space` displays the TUI popup on the active workspace interface.

---

## ⚠️ Important Gotchas for WSL Development

1. **Hotkey Listening (`pynput`) in WSL**:
   - `pynput` hooks into global system keyboard interrupts. In headless Linux/WSL environments, `pynput` requires an active X-server connection (WSLg or Windows X-Server). If running purely headless in a shell, running `shellmate-daemon` may raise `Xlib.error.DisplayNameError` if no `$DISPLAY` is set.
   - If graphical testing is blocked, you can still test all core CLI logic and the TUI app manually using the hidden `shellmate __popup` command in a TUI-supported terminal.
2. **Clipboard Copier (`pyperclip`)**:
   - On Linux systems, `pyperclip` calls `xclip` or `xsel` to sync selection sets. Ensure either of these is installed inside Ubuntu (`sudo apt install -y xclip`).
3. **YAML Loading Error Handling**:
   - Ensure the config files parse safely. The config parser contains fallback mergers, preventing errors in case the YAML gets corrupted during crash events.
