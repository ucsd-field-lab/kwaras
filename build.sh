#!/bin/bash
# Build script for Kwaras on macOS/Linux
# Usage: ./build.sh [gui|cli|both] [--clean] [--onefile]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function log_step() {
    echo -e "${CYAN}[BUILD]${NC} $1"
}

function log_done() {
    echo -e "${GREEN}[BUILD]${NC} $1"
}

function log_error() {
    echo -e "${RED}[BUILD]${NC} $1"
}

# Parse arguments
TARGET="both"
CLEAN=false
ONEFILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        gui|cli|both)
            TARGET="$1"
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --onefile)
            ONEFILE="--onefile"
            shift
            ;;
        *)
            echo "Usage: $0 [gui|cli|both] [--clean] [--onefile]"
            exit 1
            ;;
    esac
done

# Create Unix spec files
log_step "Creating Unix spec files..."

# Create gui-unix.spec
cat > gui.spec << 'SPECEOF'
# -*- mode: python -*-

block_cipher = None


a = Analysis(['gui.py'],
             pathex=['REPLACEPATH'],
             binaries=[],
             datas=[('web', 'web'), ('kwaras', 'kwaras')],
             hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.simpledialog', 'openpyxl', 'kwaras', 'kwaras.formats', 'kwaras.process', 'kwaras.formats.lift', 'kwaras.formats.xlsx', 'kwaras.formats.eaf', 'kwaras.formats.utfcsv', 'kwaras.formats.textgrid', 'kwaras.process.liftadd', 'kwaras.process.web', 'kwaras.process.timealign', 'kwaras.process.reparse', 'kwaras.langs', 'kwaras.langs.Raramuri', 'kwaras.langs.Mixtec', 'kwaras.langs.Kumiai', 'kwaras.langs.Gitonga', 'kwaras.langs.Other'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='gui',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )
SPECEOF
sed -i "s|REPLACEPATH|$PROJECT_ROOT|" gui.spec

# Create kwaras-unix.spec
cat > kwaras.spec << 'SPECEOF'
# -*- mode: python -*-

block_cipher = None


a = Analysis(['kwaras/cli.py'],
             pathex=['REPLACEPATH'],
             binaries=[],
             datas=[('web', 'web'), ('kwaras', 'kwaras')],
             hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.simpledialog', 'openpyxl', 'kwaras', 'kwaras.formats', 'kwaras.process', 'kwaras.formats.lift', 'kwaras.formats.xlsx', 'kwaras.formats.eaf', 'kwaras.formats.utfcsv', 'kwaras.formats.textgrid', 'kwaras.process.liftadd', 'kwaras.process.web', 'kwaras.process.timealign', 'kwaras.process.reparse', 'kwaras.langs', 'kwaras.langs.Raramuri', 'kwaras.langs.Mixtec', 'kwaras.langs.Kumiai', 'kwaras.langs.Gitonga', 'kwaras.langs.Other'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='kwaras',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
SPECEOF
sed -i "s|REPLACEPATH|$PROJECT_ROOT|" kwaras.spec

# Clean previous builds if requested
if [ "$CLEAN" = true ]; then
    log_step "Cleaning previous build artifacts..."
    rm -rf dist build
    log_done "Cleaned dist/ and build/"
fi

# Check and install pyinstaller
log_step "Checking pyinstaller..."
if ! command -v pyinstaller &> /dev/null; then
    log_step "Installing pyinstaller..."
    pip install "pyinstaller>=5.0,<7.0"
    log_done "pyinstaller installed"
else
    log_done "pyinstaller is installed"
fi

# Build GUI executable
if [ "$TARGET" = "gui" ] || [ "$TARGET" = "both" ]; then
    log_step "Building GUI executable..."
    pyinstaller --noconfirm --clean gui.spec $ONEFILE
    log_step "Checking build directory contents..."
    ls -la dist/
    if [ -d "dist/gui" ] && [ "$(ls -A dist/gui)" ]; then
        log_done "GUI executable created: dist/gui"
    elif [ -f "dist/gui" ]; then
        log_done "GUI executable created: dist/gui (onefile)"
    else
        log_error "GUI build failed - dist/gui directory not found"
        log_error "Contents of dist/:"
        ls -la dist/ || true
        exit 1
    fi
fi

# Build CLI executable
if [ "$TARGET" = "cli" ] || [ "$TARGET" = "both" ]; then
    log_step "Building CLI executable..."
    pyinstaller --noconfirm --clean kwaras.spec $ONEFILE
    log_step "Checking build directory contents..."
    ls -la dist/
    if [ -d "dist/kwaras" ] && [ "$(ls -A dist/kwaras)" ]; then
        log_done "CLI executable created: dist/kwaras"
    elif [ -f "dist/kwaras" ]; then
        log_done "CLI executable created: dist/kwaras (onefile)"
    else
        log_error "CLI build failed - dist/kwaras directory not found"
        log_error "Contents of dist/:"
        ls -la dist/ || true
        exit 1
    fi
fi

# Cleanup temp spec files
rm -f gui.spec kwaras.spec

echo ""
log_done "Build complete! Executables are in the dist/ directory"