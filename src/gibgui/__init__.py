from pathlib import Path
import subprocess
import shutil
import os
from .gibmacos_gui import GibMacOSGUI

def setup_environment():
    """Download original repo and apply patches"""
    original_repo = Path(__file__).parents[2] / "external" / "gibMacOS"
    
    if not original_repo.exists():
        print("Setting up gibMacOS environment...")
        original_repo.parent.mkdir(exist_ok=True)
        
        try:
            subprocess.run([
                "git", "clone", 
                "https://github.com/corpnewt/gibMacOS.git",
                str(original_repo)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Apply patches
            from .patches import apply_patches
            apply_patches(original_repo)
            
        except Exception as e:
            raise RuntimeError(f"Failed to setup environment: {str(e)}")
    
    return original_repo

def launch():
    """Package entry point"""
    setup_environment()  # Ensure environment is ready
    app = GibMacOSGUI()  # Your existing GUI class
    app.mainloop()