# Shellmate Usage Guide

Shellmate is an AI-powered terminal assistant designed to help you navigate, automate, and understand your terminal environment faster. This guide walks you through every available command and how to use it.

## Getting Started

If this is your first time using Shellmate, run the setup wizard to configure your profile and API keys:

```bash
shellmate setup
```

## Commands

### 1. `shellmate explain`
Explains a terminal error and suggests a fix.

**Usage:**
```bash
shellmate explain "error text or command output here"
```
**Example:**
```bash
shellmate explain "fatal: Not a git repository (or any of the parent directories): .git"
```

### 2. `shellmate agent`
Runs the Shellmate agentic loop to plan and execute multi-step terminal tasks. The agent will formulate a plan and ask for your approval before executing any destructive commands.

**Usage:**
```bash
shellmate agent "describe what you want to achieve"
```
**Example:**
```bash
shellmate agent "create a new React project called frontend and install tailwindcss"
```

### 3. `shellmate custom`
Manage custom parameterized commands. This is useful for saving long, frequently used commands with variables.

**Subcommands:**
- `shellmate custom list`: View all custom commands.
- `shellmate custom add`: Add a new custom command (interactive prompt).
- `shellmate custom remove <name>`: Delete a custom command.
- `shellmate custom run <name> [args]`: Execute a custom command.

**Example:**
```bash
shellmate custom add
# Name: com
# Command template: git commit -m "{message}"
# Now run it:
shellmate custom run com --message "initial commit"
```

### 4. `shellmate model`
View and manage available AI models. You can switch between different models (free and paid) depending on your needs.

**Usage:**
```bash
shellmate model list
shellmate model set <model_name>
```

### 5. `shellmate config`
View and modify your Shellmate configuration directly from the CLI.

**Usage:**
```bash
shellmate config list
shellmate config set <key> <value>
```

### 6. `shellmate profile-setup`
Interactive prompts to update your developer profile (name, preferred shell, default editor, default git branch). This helps the AI tailor its suggestions to your specific environment.

**Usage:**
```bash
shellmate profile-setup
```

### 7. `shellmate project`
Manage project contexts. This helps Shellmate understand the specific repository or directory you are working in.

**Usage:**
```bash
shellmate project setup
```

## The Shellmate Hotkey Daemon (TUI)

Shellmate includes a daemon that listens for a global hotkey to instantly open a terminal UI (TUI) popup. This is perfect for quick queries without leaving your current terminal session.

**To start the daemon:**
```bash
shellmate-daemon
```

**Using the TUI:**
1. Press `Ctrl+\` (Control + Backslash) anywhere to open the Shellmate TUI.
2. Type your question (e.g., "how to untar a file").
3. The AI will suggest a command.
4. Press `Enter` to copy the command to your clipboard and close the popup, or press `Ctrl+C` to copy without closing.

*Note for WSL users:* If you do not have an X server (like WSLg) running, the global hotkey cannot listen in the background. In this case, `shellmate-daemon` will run in terminal mode — simply press `Enter` in that terminal window to open the TUI.

**To run the TUI popup directly for testing:**
```bash
python3 -c "from shellmate.tui.popup import run_popup; run_popup()"
```

