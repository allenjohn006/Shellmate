from setuptools import setup, find_packages

setup(
    name="shellmate",
    version="0.1.0",
    description="AI-powered terminal assistant for Linux and WSL",
    packages=find_packages(),
    install_requires=[
        "typer",
        "rich",
        "textual",
        "pynput",
        "pyyaml",
        "requests",
        "pyperclip"
    ],
    entry_points={
        "console_scripts": [
            "shellmate=shellmate.main:app",
            "shellmate-daemon=shellmate.daemon.hotkey:start",
        ],
    },
)
