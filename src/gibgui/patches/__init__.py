from pathlib import Path
import shutil
import os

def apply_patches(target_dir):
    """Copy modified files to the original repo"""
    patches_dir = Path(__file__).parent
    
    # Patch download.py
    script_dir = target_dir / "Scripts"
    script_dir.mkdir(exist_ok=True)
    shutil.copy(
        patches_dir / "download.py",
        script_dir / "download.py"
    )
    
    print("Successfully applied patches")