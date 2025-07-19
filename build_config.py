# Build configuration for Capitulador packaging

import sys
from pathlib import Path

# PyInstaller configuration for executable creation
APP_NAME = "Capitulador"
MAIN_SCRIPT = "gui_capitulador.py"
ICON_FILE = None  # Add icon path if available

# Additional files to include in distribution
ADDITIONAL_FILES = [
    ("config/dev.env", "config/"),
    ("README.md", "."),
    ("LICENSE", "."),
]

# Hidden imports required for application
HIDDEN_IMPORTS = [
    "tkinter",
    "tkinter.ttk",
    "pydantic",
    "pathlib",
    "subprocess",
    "threading",
]

# Modules to exclude from build
EXCLUDES = [
    "numpy",
    "matplotlib",
    "scipy",
    "pandas",
]

# Build configuration settings
BUILD_CONFIG = {
    "onefile": True,
    "windowed": True,
    "name": APP_NAME,
    "clean": True,
    "noconfirm": True,
}

def get_build_command():
    # Generate PyInstaller command with all configuration options
    cmd = ["pyinstaller"]
    
    if BUILD_CONFIG["onefile"]:
        cmd.append("--onefile")
    
    if BUILD_CONFIG["windowed"]:
        cmd.append("--windowed")
    
    if BUILD_CONFIG["clean"]:
        cmd.append("--clean")
    
    if BUILD_CONFIG["noconfirm"]:
        cmd.append("--noconfirm")
    
    cmd.extend([
        "--name", BUILD_CONFIG["name"],
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", ".",
    ])
    
    # Add additional files to distribution
    for src, dst in ADDITIONAL_FILES:
        cmd.extend(["--add-data", f"{src}{':' if sys.platform != 'win32' else ';'}{dst}"])
    
    # Add hidden imports
    for module in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", module])
    
    # Add module exclusions
    for module in EXCLUDES:
        cmd.extend(["--exclude-module", module])
    
    if ICON_FILE:
        cmd.extend(["--icon", ICON_FILE])
    
    cmd.append(MAIN_SCRIPT)
    
    return cmd

if __name__ == "__main__":
    print("Build command:")
    print(" ".join(get_build_command()))
