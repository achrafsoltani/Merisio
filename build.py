#!/usr/bin/env python3
"""Build script for AnalyseSI Modern."""

import os
import sys
import platform
import subprocess
import shutil

APP_NAME = "Merisio"
VERSION = "1.1.0"


def clean():
    """Clean build directories."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for d in dirs_to_clean:
        if os.path.exists(d):
            print(f"Removing {d}/")
            shutil.rmtree(d)

    # Clean .pyc files
    for root, dirs, files in os.walk('.'):
        for f in files:
            if f.endswith('.pyc'):
                os.remove(os.path.join(root, f))


def build():
    """Build the application."""
    system = platform.system().lower()

    print(f"Building {APP_NAME} v{VERSION} for {system}...")

    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

    # Build command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'merisio.spec'
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\nBuild successful!")
        print(f"Output: dist/{APP_NAME}")

        if system == 'linux':
            print(f"\nTo run: ./dist/{APP_NAME}")
        elif system == 'windows':
            print(f"\nTo run: dist\\{APP_NAME}.exe")
        elif system == 'darwin':
            print(f"\nTo run: open dist/{APP_NAME}.app")
    else:
        print("Build failed!")
        sys.exit(1)


def create_windows_ico():
    """Create Windows .ico file from SVG (requires inkscape or imagemagick)."""
    svg_path = "resources/icons/app_icon.svg"
    ico_path = "resources/icons/app_icon.ico"

    if not os.path.exists(svg_path):
        print(f"SVG not found: {svg_path}")
        return False

    # Try using ImageMagick
    try:
        subprocess.run([
            'convert', '-background', 'none',
            svg_path,
            '-define', 'icon:auto-resize=256,128,64,48,32,16',
            ico_path
        ], check=True)
        print(f"Created {ico_path}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ImageMagick not found. Install it to create .ico files.")
        print("  Ubuntu/Debian: sudo apt install imagemagick")
        print("  Windows: choco install imagemagick")
        return False


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'clean':
            clean()
        elif cmd == 'build':
            build()
        elif cmd == 'ico':
            create_windows_ico()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python build.py [clean|build|ico]")
    else:
        build()
