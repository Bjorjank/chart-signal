import os
import subprocess
import sys

def setup_project():
    print("Setting up Trading Chart App...")
    
    # Create folders
    folders = ['static', 'templates', 'data']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"✅ Created folder: {folder}")
    
    # Install requirements
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "pandas", "numpy", "python-multipart"])
    
    print("✅ Setup complete! Run: python main.py")

if __name__ == "__main__":
    setup_project()