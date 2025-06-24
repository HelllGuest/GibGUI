#!/usr/bin/env python3
"""
Title: GibMacOS GUI Bootstrap
Description: Automates setup and integration of gibMacOS GUI
Features:
  - Clones/updates original gibMacOS repository
  - Copies GUI components to target directory
  - Handles cross-platform execution
  - Auto-updates on launch
Usage: Execute directly: `python run_gui.py`
Dependencies: Python 3.8+, git, requests
License: MIT
Author: Anoop Kumar
Date: 24/06/2025 (DD/MM/YYYY)
"""

import os
import sys
import shutil
import subprocess
import platform

GIB_REPO_URL = "https://github.com/corpnewt/gibMacOS"
GIB_DIR = "gibMacOS"


def main():
    # Clone/update gibMacOS
    if not setup_gib_repo():
        sys.exit(1)

    # Copy modified files
    if not copy_custom_files():
        sys.exit(1)

    # Launch GUI
    launch_gui()


def setup_gib_repo():
    if not os.path.exists(GIB_DIR):
        print("Cloning gibMacOS repository...")
        result = subprocess.run(["git", "clone", GIB_REPO_URL, GIB_DIR])
        if result.returncode != 0:
            print("Error cloning repository")
            return False

    os.chdir(GIB_DIR)
    print("Updating gibMacOS repository...")
    result = subprocess.run(["git", "pull"])
    os.chdir("..")
    return result.returncode == 0


def copy_custom_files():
    try:
        # Copy GUI script
        shutil.copy("gibmacos_gui.py", os.path.join(GIB_DIR, "gibmacos_gui.py"))
        # Copy modified downloader
        os.makedirs(os.path.join(GIB_DIR, "Scripts"), exist_ok=True)
        shutil.copy(
            os.path.join("Scripts", "downloader.py"),
            os.path.join(GIB_DIR, "Scripts", "downloader.py"),
        )
        return True
    except Exception as e:
        print(f"File copy failed: {str(e)}")
        return False


def launch_gui():
    os.chdir(GIB_DIR)
    command = [sys.executable, "gibmacos_gui.py"]

    # Special handling for macOS .command files
    if platform.system() == "Darwin":
        subprocess.run(["chmod", "+x", "gibmacos_gui.py"])
        command = ["./gibmacos_gui.py"]

    subprocess.run(command)


if __name__ == "__main__":
    main()
