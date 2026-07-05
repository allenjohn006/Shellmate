import os
import yaml
from pathlib import Path
from .config import CONFIG_DIR, ensure_config_dir

CUSTOMS_FILE = CONFIG_DIR / "customs.yaml"

def load_customs() -> list:
    if not CUSTOMS_FILE.exists():
        return []
    try:
        with open(CUSTOMS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_customs(customs: list):
    ensure_config_dir()
    with open(CUSTOMS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(customs, f, default_flow_style=False)

def get_custom(name: str) -> dict:
    for c in load_customs():
        if c.get("name") == name:
            return c
    return None

def add_custom(custom_cmd: dict):
    customs = load_customs()
    # Replace if exists
    for i, c in enumerate(customs):
        if c.get("name") == custom_cmd.get("name"):
            customs[i] = custom_cmd
            save_customs(customs)
            return
    customs.append(custom_cmd)
    save_customs(customs)

def remove_custom(name: str) -> bool:
    customs = load_customs()
    new_customs = [c for c in customs if c.get("name") != name]
    if len(new_customs) != len(customs):
        save_customs(new_customs)
        return True
    return False
