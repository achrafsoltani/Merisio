#!/usr/bin/env python3
"""Build script for Merisio."""

import os
import sys
import platform
import subprocess
import shutil

APP_NAME = "Merisio"
CLI_NAME = "merisio-cli"
VERSION = "1.3.1"


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


def _ensure_pyinstaller():
    """Ensure PyInstaller is installed."""
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])


def build():
    """Build the GUI application."""
    system = platform.system().lower()

    print(f"Building {APP_NAME} v{VERSION} for {system}...")
    _ensure_pyinstaller()

    # Determine icon path
    if system == 'windows':
        icon_path = 'resources/icons/app_icon.ico'
        if not os.path.exists(icon_path):
            icon_path = 'resources/icons/app_icon.png'
    else:
        icon_path = 'resources/icons/app_icon.png'

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--name', APP_NAME,
        '--add-data', f'resources/icons/app_icon.svg{os.pathsep}resources/icons',
        '--add-data', f'resources/icons/app_icon.png{os.pathsep}resources/icons',
        '--hidden-import', 'PySide6.QtCore',
        '--hidden-import', 'PySide6.QtGui',
        '--hidden-import', 'PySide6.QtWidgets',
    ]

    if os.path.exists(icon_path):
        cmd.extend(['--icon', icon_path])

    cmd.append('main.py')

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\nBuild successful!")
        print(f"Output: dist/{APP_NAME}")
    else:
        print("Build failed!")
        sys.exit(1)


def build_cli():
    """Build the CLI tool."""
    system = platform.system().lower()

    print(f"Building {CLI_NAME} v{VERSION} for {system}...")
    _ensure_pyinstaller()

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        '--onefile',
        '--console',
        '--name', CLI_NAME,
        '--hidden-import', 'PySide6.QtCore',
        '--hidden-import', 'PySide6.QtGui',
        '--hidden-import', 'PySide6.QtWidgets',
        '--hidden-import', 'PySide6.QtSvg',
        'cli.py',
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\nBuild successful!")
        print(f"Output: dist/{CLI_NAME}")
    else:
        print("CLI build failed!")
        sys.exit(1)


def build_all():
    """Build both GUI and CLI."""
    build()
    build_cli()


def install_man():
    """Install man pages to /usr/share/man/man1/."""
    man_dir = "/usr/share/man/man1"
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "man")

    pages = ["merisio.1", "merisio-cli.1"]
    for page in pages:
        src = os.path.join(src_dir, page)
        if not os.path.isfile(src):
            print(f"Man page not found: {src}")
            sys.exit(1)
        dst = os.path.join(man_dir, page)
        print(f"Installing {src} -> {dst}")
        shutil.copy2(src, dst)

    print("Updating man database...")
    subprocess.run(["mandb", "-q"])
    print("Man pages installed.")


def uninstall_man():
    """Remove installed man pages."""
    man_dir = "/usr/share/man/man1"
    pages = ["merisio.1", "merisio-cli.1"]
    for page in pages:
        path = os.path.join(man_dir, page)
        if os.path.isfile(path):
            print(f"Removing {path}")
            os.remove(path)
        else:
            print(f"Not found: {path}")

    print("Updating man database...")
    subprocess.run(["mandb", "-q"])
    print("Man pages uninstalled.")


def create_windows_ico():
    """Create Windows .ico file from PNG (requires ImageMagick)."""
    png_path = "resources/icons/app_icon.png"
    ico_path = "resources/icons/app_icon.ico"

    if not os.path.exists(png_path):
        print(f"PNG not found: {png_path}")
        return False

    # Try using ImageMagick
    try:
        subprocess.run([
            'convert', png_path,
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
        elif cmd == 'build-cli':
            build_cli()
        elif cmd == 'build-all':
            build_all()
        elif cmd == 'ico':
            create_windows_ico()
        elif cmd == 'install-man':
            install_man()
        elif cmd == 'uninstall-man':
            uninstall_man()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python build.py [clean|build|build-cli|build-all|ico|install-man|uninstall-man]")
    else:
        build_all()
