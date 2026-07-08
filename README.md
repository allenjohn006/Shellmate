# Shellmate 

Shellmate is a robust, developer-focused, AI-powered terminal assistant built specifically for **Linux** and **WSL (Windows Subsystem for Linux)**. It runs directly in your terminal, suggesting shell commands, explaining errors, and orchestrating multi-step agentic tasks with user-approved execution. It also includes a global-hotkey-triggered Textual TUI (Terminal User Interface) popup for interactive, context-aware assistance.

---

## Features

- **Inline AI Assistant**: Ask questions in plain English and receive instant commands, full explanations, and alternative suggestions.
- **Context-Aware**: Reads the last few commands in your shell history (`bash`, `zsh`, or `fish`) and parses optional project-specific `.shellmate` files to provide contextually accurate solutions.
- **Smart Error Explanations**: Pipe or paste command line errors to receive an explanation and a suggested fix command.
- **Interactive Agent Mode**: Provide a complex goal, and watch Shellmate plan it step-by-step. Approvals are checked per command, with execution feedback piped back to the AI for dynamic self-correction and plan adjustments.
- **Custom Commands (Templates)**: Create, list, edit, and remove parameterized templates. Shellmate automatically detects variables (e.g. `{branch}`, `{message}`) and prompt-fills them.
- **TUI Chat Popup**: Press `Ctrl+Space` anytime (runs via a background hotkey daemon) to open a beautiful, floating Textual chat application. Press `Enter` on any suggestion card to copy and close or `Tab` to copy and keep chatting.
- **Model Switching**: Switch between free and paid models hosted on OpenRouter, Anthropic, OpenAI, or Google Gemini.
- **Safety First**: Destructive commands (e.g., `rm -rf`, `chmod 777`, `mkfs`) are auto-classified and require explicit double-confirmation (`YES`) before running.

---

## Project Structure

```text
shellmate/
  ├── __init__.py
  ├── main.py                  # Typer CLI entrypoint & commands
  ├── core/
  │     ├── __init__.py
  │     ├── ai.py              # LLM client wrapper (OpenRouter, OpenAI, Anthropic, Gemini)
  │     ├── config.py          # Config read/write (~/.shellmate/config.yaml)
  │     ├── customs.py         # Custom command templates (~/.shellmate/customs.yaml)
  │     ├── context.py         # Shell history, .shellmate project parser & OS detection
  │     ├── executor.py        # Subprocess execution, destructive command checks
  │     └── agent.py           # Multi-step agent execution loop
  ├── tui/
  │     ├── __init__.py
  │     ├── popup.py           # Textual TUI chat window
  │     └── styles.css         # Textual CSS styles
  ├── daemon/
  │     ├── __init__.py
  │     └── hotkey.py          # pynput keyboard hook listener for Ctrl+Space
  └── utils/
        ├── __init__.py
        └── models.py          # Configuration lists of free and paid models
```

---

## Setup & Installation

### 1. Prerequisites
- Python 3.8+
- Active internet connection for API requests
- Linux or WSL2 (Ubuntu / Debian / etc.)
- Clipboard utility installed:
  - For WSL: Windows Clipboard is automatically accessed.
  - For Linux: Ensure `xclip` or `xsel` is installed (`sudo apt install xclip`).

### 2. Install Shellmate
Clone the repository and install it in editable mode:
```bash
git clone https://github.com/allenjohn006/Shellmate.git
cd shellmate
pip install -e .
```

### 3. Run the Onboarding Wizard
To configure your assistant and install the shell aliases/daemon hooks:
```bash
shellmate setup
```
The setup wizard will:
- Collect your developer profile (name, shell, favorite editor, git branch).
- Guide you to enter your API key for OpenRouter (recommended), OpenAI, Anthropic, or Google Gemini.
- Allow you to pick a models-tier (free/paid).
- Auto-inject startup hooks into your shell configuration (`~/.bashrc`, `~/.zshrc`, or `~/.config/fish/config.fish`).
- Save the configuration file locally to `~/.shellmate/config.yaml`.

*Note: Reload your shell (`source ~/.bashrc` or restart the terminal) to apply the hotkey daemon and alias.*

---

## CLI Usage Guide

Shellmate uses the alias `sm` for speed, but you can also use `shellmate` directly.

### 1. Ask Inline Questions
Simply ask Shellmate how to do something.
```bash
sm "extract a tar.gz archive to a specific folder"
```

### 2. Explain Errors
Explain what went wrong with a program and suggest a command to fix it.
```bash
sm explain "npm ERR! code EACCES syscall access path /usr/local/lib/node_modules"
```

### 3. Agent Mode (Autonomous Executions)
Provide a goal, and Shellmate will generate a multi-step execution plan. It prompts you before running every step.
```bash
sm agent "find all .py files in this folder, search for lines containing 'import os', and print them"
```
**Options:**
- `--dry-run`: View the plans and steps the AI would execute without invoking any of the commands.

### 4. Custom Templates
Manage and run reusable command templates:
- **Add**: Interactive creation.
  ```bash
  sm custom add
  # Follow prompts to set name, description, and command (e.g. "git commit -m '{message}'")
  ```
- **List**: Print a clean, formatted table.
  ```bash
  sm custom list
  ```
- **Run**: Directly run a custom command. You can pass variables as key=value pairs, double-dash arguments, or omit them to be prompted interactively.
  ```bash
  sm custom run <name> [variables...]
  
  # Examples:
  sm custom run commit --message "fixed index lock"
  sm custom run commit message="resolved lock issue"
  ```
- **Edit**: Edit an existing custom command template.
  ```bash
  sm custom edit <name>
  ```
- **Remove**: Safely delete a template.
  ```bash
  sm custom remove <name>
  ```

### 5. Managing Models
List models, view current selections, and change them on the fly:
```bash
sm model list
sm model set <model-name>
```

### 6. Configurations
Inspect or modify settings directly from the terminal without editing YAML:
```bash
sm config list
sm config set api_key "sk-or-your-new-key"
```

### 7. Profile Setup
Update your shell preferences, favorite editors, or git branches:
```bash
sm profile setup
```

### 8. Project Configurations
You can register multiple project templates inside `~/.shellmate/projects/` or save a local `.shellmate` file in your workspace directory to customize suggestions:
```bash
sm project add
sm project list
```
**Example `.shellmate` structure:**
```yaml
project: backend-api
stack: FastAPI + PostgreSQL
scripts:
  start: uvicorn main:app --reload
  test: pytest
```

---

## TUI Chat & Global Hotkey Daemon

The hotkey daemon listens globally for `Ctrl+Space`. When pressed, it triggers a floating overlay chat:
- **Keyboard Shortcuts**:
  - `Escape`: Close/Hide TUI popup.
  - `Tab` (on suggestions): Copies the command to your clipboard.
  - `Enter` (on suggestions): Copies the command and closes the TUI so you can immediately paste it.

To run/restart the daemon manually in the background:
```bash
shellmate-daemon &
```

---

## Configuration File Schema
All configurations are saved in yaml format inside `~/.shellmate/config.yaml`:
```yaml
name: Allen
preferred_shell: bash
editor: code
default_branch: main
provider: openrouter
api_key: sk-or-xxxxxxxxxxxxxxxx
quick_model: google/gemini-2.0-flash-exp:free
agent_model: deepseek/deepseek-r1:free
theme: dark
always_confirm_destructive: true
dry_run: false
```
