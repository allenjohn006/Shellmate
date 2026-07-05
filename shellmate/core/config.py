import os
import yaml
from pathlib import Path

CONFIG_DIR = Path.home() / ".shellmate"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "name": "User",
    "preferred_shell": "bash",
    "editor": "nano",
    "default_branch": "main",
    "provider": "openrouter",
    "api_key": "",
    "quick_model": "google/gemini-2.0-flash-exp:free",
    "agent_model": "deepseek/deepseek-r1:free",
    "theme": "dark",
    "always_confirm_destructive": True,
    "dry_run": False
}

def ensure_config_dir():
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if not config:
                return DEFAULT_CONFIG.copy()
            
            # Merge with defaults to ensure all keys exist
            merged = DEFAULT_CONFIG.copy()
            merged.update(config)
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)

def get_config_value(key: str, default=None):
    config = load_config()
    return config.get(key, default)

def set_config_value(key: str, value):
    config = load_config()
    config[key] = value
    save_config(config)

def is_setup_complete() -> bool:
    return CONFIG_FILE.exists()
