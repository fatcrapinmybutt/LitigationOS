import subprocess
import sys
import shutil

def ensure_pyinstaller():
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def compile_spec():
    print("Running: pyinstaller fredexespec.py")
    result = subprocess.run(["pyinstaller", "fredexespec.py"])
    if result.returncode == 0:
        print("✅ .exe compiled successfully.")
    else:
        print("❌ Compilation failed.")

def main():
    ensure_pyinstaller()
    compile_spec()

if __name__ == "__main__":
    main()
