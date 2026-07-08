"""
Test script to verify all shellmate imports and TUI compatibility with installed Textual version.
Run with: python3 /tmp/sm_test.py
"""
import sys

results = []

# 1. Test textual version
try:
    import textual
    results.append(f"[OK] textual version: {textual.__version__}")
except Exception as e:
    results.append(f"[FAIL] textual import: {e}")

# 2. Test work decorator import (new location in textual 8.x)
try:
    from textual._work_decorator import work
    results.append("[OK] work from textual._work_decorator")
except Exception as e:
    results.append(f"[FAIL] work import: {e}")

# 3. Test call_from_thread on App
try:
    from textual.app import App
    has_cft = hasattr(App, "call_from_thread")
    results.append(f"[{'OK' if has_cft else 'FAIL'}] App.call_from_thread exists: {has_cft}")
except Exception as e:
    results.append(f"[FAIL] App check: {e}")

# 4. Test worker thread parameter
try:
    from textual._work_decorator import work as w
    import inspect
    sig = inspect.signature(w)
    has_thread = "thread" in sig.parameters
    results.append(f"[{'OK' if has_thread else 'FAIL'}] work() has 'thread' param: {has_thread}")
except Exception as e:
    results.append(f"[FAIL] work signature: {e}")

# 5. Test pyperclip
try:
    import pyperclip
    results.append("[OK] pyperclip imported")
except Exception as e:
    results.append(f"[FAIL] pyperclip: {e}")

# 6. Test shellmate core imports
try:
    from shellmate.core.ai import query_ai
    results.append("[OK] shellmate.core.ai")
except Exception as e:
    results.append(f"[FAIL] shellmate.core.ai: {e}")

try:
    from shellmate.core.context import get_shell_history
    results.append("[OK] shellmate.core.context")
except Exception as e:
    results.append(f"[FAIL] shellmate.core.context: {e}")

# 7. Test the popup module import (the big one)
try:
    from shellmate.tui import popup
    results.append("[OK] shellmate.tui.popup imported successfully")
    results.append(f"[OK] run_popup function exists: {hasattr(popup, 'run_popup')}")
except Exception as e:
    results.append(f"[FAIL] shellmate.tui.popup: {e}")

# 8. Test daemon hotkey import
try:
    from shellmate.daemon import hotkey
    results.append("[OK] shellmate.daemon.hotkey imported")
except Exception as e:
    results.append(f"[FAIL] daemon hotkey: {e}")

# 9. Check Static | None type hint compatibility (Python 3.9 vs 3.10+)
py_ver = sys.version_info
results.append(f"[INFO] Python version: {py_ver.major}.{py_ver.minor}.{py_ver.micro}")
if py_ver < (3, 10):
    results.append("[WARN] Python < 3.10: 'Static | None' type hints require 'from __future__ import annotations' or Optional[]")

print("\n".join(results))
