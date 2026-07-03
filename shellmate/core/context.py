import os
import yaml
from pathlib import Path

def get_shell_history(n=5) -> list:
    """Reads the last n commands from the user's shell history."""
    shell = os.environ.get("SHELL", "")
    home = Path.home()
    history_file = None
    
    if "bash" in shell:
        history_file = home / ".bash_history"
    elif "zsh" in shell:
        history_file = home / ".zsh_history"
    elif "fish" in shell:
        history_file = home / ".local" / "share" / "fish" / "fish_history"
        
    if not history_file or not history_file.exists():
        return []
        
    try:
        # Some history files can have weird encodings, ignoring errors is safest
        with open(history_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.read().splitlines()
            
        # Clean up history lines based on shell specifics if needed
        # (e.g. zsh adds timestamps: `: 1612345678:0;cmd`)
        cleaned = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "zsh" in shell and line.startswith(":"):
                parts = line.split(";", 1)
                if len(parts) == 2:
                    line = parts[1]
            elif "fish" in shell and line.startswith("- cmd:"):
                line = line.replace("- cmd:", "").strip()
            # Ignore fish timestamp lines
            if "fish" in shell and line.startswith("when:"):
                continue
                
            cleaned.append(line)
            
        return cleaned[-n:]
    except Exception:
        return []

def get_project_context() -> dict:
    """Checks the current directory for a .shellmate file."""
    project_file = Path.cwd() / ".shellmate"
    if not project_file.exists():
        return None
        
    try:
        with open(project_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None

def detect_os() -> str:
    """Detects if we are running in WSL or native Linux."""
    try:
        with open("/proc/version", "r") as f:
            version_info = f.read().lower()
            if "microsoft" in version_info:
                return "wsl"
    except Exception:
        pass
    
    return "linux"
