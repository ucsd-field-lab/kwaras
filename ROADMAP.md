# Kwaras Modernization & Reliability Recommendations

## Executive Summary

The Kwaras project uses solid foundational technologies but relies on several deprecated/aging patterns. Implementation of these recommendations will improve reliability, maintainability, cross-platform compatibility, and support for Python 3.10+ (py2exe/py2app break in Python 3.12+).

---

## 1. CRITICAL: Build System and Executable Generation

### Current Issues
- **Using deprecated `distutils`** (removed in Python 3.12, breaking builds)
- **Using deprecated `py2exe`/`py2app`** (last major updates 2015+, limited Python support)
- Build process will fail on modern Python versions

### Recommendations

#### 1.1 Migrate Package Configuration to Modern setuptools
**Priority: CRITICAL**

Replace `distutils` with `setuptools`:

```python
# setup.py - Updated approach
from setuptools import setup, find_packages
from pathlib import Path

VERSION = '3.0.0rc2'

setup(
    name='kwaras',
    version=VERSION,
    packages=find_packages(),  # Auto-discover packages
    python_requires='>=3.8',   # Explicit Python version support
    install_requires=[
        'openpyxl>=3.0',        # Explicit version constraints
    ],
    entry_points={              # Modern CLI approach
        'console_scripts': [
            'kwaras-gui=kwaras.gui:main',
            'kwaras-lexicon=kwaras.gui:convert_lexicon',
        ],
    },
    # ... rest of metadata
)
```

#### 1.2 Migrate to PyInstaller for Executable Generation
**Priority: HIGH**

Replace `py2exe`/`py2app` with **PyInstaller** (actively maintained, supports Python 3.9-3.11+):

**Installation:**
```bash
pip install pyinstaller
```

**Build command (cross-platform):**
```bash
pyinstaller --onefile --windowed --name kwaras gui.py
```

**Benefits:**
- Single tool for Windows, macOS, Linux
- Supports modern Python versions (3.9-3.12+)
- Better dependency bundling
- More reliable executable generation

**Create `pyinstaller_build.spec`:**
```python
# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[('web', 'web'), ('kwaras', 'kwaras')],
    hiddenimports=['openpyxl'],
    hookspath=[],
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
          [],
          name='kwaras',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,  # No console window
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
)

coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='kwaras',
)
```

#### 1.3 Update `setup.py` to Modern Approach
**Priority: HIGH**

```python
# New setup.py structure
from setuptools import setup, find_packages
from pathlib import Path

# Read version from source
version = "3.0.0rc2"

# Gather data files programmatically
def collect_data_files(base_dir, pattern):
    """Safely collect data files matching pattern."""
    from pathlib import Path
    base = Path(base_dir)
    return [str(f) for f in base.rglob(pattern)]

setup(
    name='kwaras',
    version=version,
    author='Lucien Carroll',
    author_email='lucien@discurs.us',
    description='Tools for managing ELAN corpus files',
    long_description=Path('README.md').read_text(),
    long_description_content_type='text/markdown',
    url='http://github.com/ucsd-field-lab/kwaras',
    license='MIT',
    packages=find_packages(exclude=['tests', 'build', 'dist']),
    python_requires='>=3.8, <3.13',
    install_requires=[
        'openpyxl>=3.0',
    ],
    extras_require={
        'dev': ['pytest', 'pytest-cov', 'pyinstaller'],
        'build': ['pyinstaller'],
    },
    entry_points={
        'console_scripts': [
            'kwaras=kwaras.gui:main',
        ],
    },
    package_data={
        'kwaras': [
            'web/**/*.html',
            'web/**/*.css',
            'web/**/*.js',
            'web/**/*.png',
        ],
    },
)
```

---

## 2. FILE HANDLING: Resource Leaks and Cross-Platform Issues

### Current Issues

```python
# ❌ BAD - Resource leaks, not cross-platform
cfg = json.load(open("lexicon.cfg"))  # File never closed
cfgstr = ''.join(list(open(cfg_file)))  # File never closed
```

### Recommendations

#### 2.1 Use Context Managers Everywhere
**Priority: HIGH**

```python
# ✅ GOOD - Automatic resource cleanup
import json
from pathlib import Path

def load_config(config_file):
    """Safely load JSON configuration."""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

# Update in gui.py
cfg = load_config("lexicon.cfg")
```

#### 2.2 Replace `os.path` with `pathlib.Path`
**Priority: MEDIUM**

```python
# ❌ OLD
import os.path
dir_name = cfg["EAFL_DIR"]
inf_name = cfg["LIFT"]
base, ext = os.path.splitext(inf_name)
outf_name = os.path.join(dir_name, base + "-guid.lift")

# ✅ NEW - Cross-platform, more readable
from pathlib import Path

def process_lift_file(config):
    """Process LIFT lexicon file."""
    dir_path = Path(config["EAFL_DIR"])
    input_file = Path(config["LIFT"])
    
    if not input_file.suffix.lower() == ".lift":
        raise ValueError(f"Expected .lift file, got {input_file.suffix}")
    
    # Generate output paths
    output_paths = {
        'guid': dir_path / f"{input_file.stem}-guid.lift",
        'added': dir_path / f"{input_file.stem}-added.lift",
        'eafl': dir_path / f"{input_file.stem}-import.eafl",
    }
    
    return input_file, output_paths
```

#### 2.3 Add File Validation
**Priority: HIGH**

```python
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def validate_input_file(filepath, extensions):
    """Validate that input file exists and has correct extension."""
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if not path.suffix.lower() in extensions:
        raise ValueError(
            f"Expected extension in {extensions}, got {path.suffix}"
        )
    
    return path

def ensure_output_dir(dirpath):
    """Ensure output directory exists."""
    path = Path(dirpath)
    path.mkdir(parents=True, exist_ok=True)
    return path
```

---

## 3. ERROR HANDLING: Robustness Improvements

### Current Issues

```python
# ❌ BAD - Bare except swallows all errors, including interrupts
except Exception as err:
    print(traceback.format_exc())
    # No recovery mechanism
    raise err

# ❌ BAD - No validation of config values
cfg = json.load(open(cfg_path))  # What if required keys missing?
dir_name = cfg["EAFL_DIR"]  # KeyError if missing
```

### Recommendations

#### 3.1 Use Specific Exception Handling
**Priority: MEDIUM**

```python
import logging
import sys

logger = logging.getLogger(__name__)

def export_corpus(cfg_path):
    """Export corpus with proper error handling."""
    try:
        config = load_config(cfg_path)
        validate_config(config, required_keys=['EAFL_DIR', 'LIFT'])
        return process_lexicon(config)
    
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {cfg_path}")
        raise
    
    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        raise
    
    except Exception as e:  # Only catch truly unexpected errors
        logger.exception(f"Unexpected error during corpus export: {e}")
        raise
```

#### 3.2 Add Configuration Validation
**Priority: HIGH**

```python
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def validate_config(config: Dict[str, Any], required_keys: List[str]) -> None:
    """Validate configuration has all required keys."""
    missing_keys = set(required_keys) - set(config.keys())
    if missing_keys:
        raise ValueError(
            f"Configuration missing required keys: {', '.join(missing_keys)}"
        )

def validate_paths(config: Dict[str, Any], path_keys: List[str]) -> None:
    """Validate that all path values exist."""
    from pathlib import Path
    
    for key in path_keys:
        if key not in config:
            continue
        
        path = Path(config[key])
        if not path.exists():
            raise FileNotFoundError(
                f"Path configured for '{key}' does not exist: {path}"
            )
```

---

## 4. TYPE SAFETY: Add Type Hints

### Current Issues
- No type hints anywhere in codebase
- Makes code harder to understand and maintain
- IDE/linter support is limited

### Recommendations

#### 4.1 Add Comprehensive Type Hints
**Priority: MEDIUM**

```python
# gui.py - Add type hints
from typing import Optional, Dict, Any
import argparse

def convert_lexicon(config_path: str) -> None:
    """Convert FLEx LIFT lexicon to EAFL format.
    
    Args:
        config_path: Path to lexicon configuration file
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If LIFT file has wrong format
    """
    from kwaras.conf import config
    from kwaras.formats.lift import Lift
    from kwaras.process import liftadd
    
    cfg = load_config(config_path)
    # ... rest of implementation

def export_corpus(cfg_path: Optional[str] = None) -> None:
    """Export ELAN corpus to web interface."""
    # ... implementation

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='ELAN Corpus Tools')
    # ... argument setup
    return parser.parse_args()
```

#### 4.2 Add Type Hints to Classes
**Priority: MEDIUM**

```python
# formats/lift.py
from typing import Dict, Tuple, Optional
from pathlib import Path
import xml.etree.ElementTree as ET

class Lift:
    """LIFT (Lexical Interchange Format) lexicon processor."""
    
    def __init__(self, filename: str) -> None:
        """Initialize LIFT processor with lexicon file.
        
        Args:
            filename: Path to LIFT lexicon file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not valid LIFT format
        """
        self.path = Path(filename)
        if not self.path.exists():
            raise FileNotFoundError(f"Lexicon file not found: {filename}")
        
        self.tree: ET.ElementTree = ET.parse(filename)
        self.root: ET.Element = self.tree.getroot()
        self.lexemes: Dict[Tuple[str, int], str] = {}
        self._load_lexemes()
    
    def _load_lexemes(self) -> None:
        """Load lexeme entries from XML tree."""
        entries = self.root.findall("entry")
        for node in entries:
            # ... implementation
    
    def getEntry(self, guid: str) -> Optional[ET.Element]:
        """Look up a lexical entry by GUID."""
        guid = guid.split("_")[-1]
        entry = self.root.find(f"entry[@guid='{guid}']")
        return entry
    
    def getField(self, guid: str, field: str) -> Optional[ET.Element]:
        """Get attribute node of entry."""
        # ... implementation
```

---

## 5. LOGGING: Replace Print Statements

### Current Issues

```python
# ❌ BAD - No way to control output, no timestamps
print("Exposing GUID as field in", inf_name)
print("Adding allomorphs to", inf_name)
print("Data written to", outf_name)
```

### Recommendations

#### 5.1 Add Structured Logging
**Priority: HIGH**

```python
import logging
from pathlib import Path

# Create module logger
logger = logging.getLogger(__name__)

def convert_lexicon(config_path: str) -> None:
    """Convert LIFT to EAFL with logging."""
    logger.info(f"Starting lexicon conversion from config: {config_path}")
    
    try:
        cfg = load_config(config_path)
        lift = Lift(cfg["LIFT"])
        logger.debug(f"Loaded LIFT lexicon: {cfg['LIFT']}")
        
        logger.info("Exposing GUID as field in lexicon")
        lift = lift.exposeGuid()
        
        logger.info(f"Writing GUID-exposed lexicon to {cfg['EAFL_DIR']}")
        lift.write(...)
        
        logger.info("Lexicon conversion completed successfully")
        
    except Exception as e:
        logger.exception(f"Lexicon conversion failed: {e}")
        raise

# Setup logging in main entry point
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
```

#### 5.2 Add Debug Logging for Development
**Priority: LOW**

```python
logger.debug(f"Entry GUID: {eid}, Key: {key}")
logger.debug(f"Processing variant entries: {len(variants)}")
```

---

## 6. DEPENDENCIES: Add Version Constraints

### Current Issues

```python
# requirements.txt - No version constraints
py2exe          # Broken on Python 3.12+

# setup.py
install_requires=['openpyxl'],  # No version constraint
```

### Recommendations

#### 6.1 Update `requirements.txt`
**Priority: HIGH**

```ini
# requirements.txt - Production dependencies
openpyxl>=3.0,<4.0
lxml>=4.9  # Optional, for better XML handling

# requirements-build.txt - Build-only dependencies
pyinstaller>=5.0,<7.0
setuptools>=65.0
wheel>=0.38

# requirements-dev.txt - Development dependencies
pytest>=7.0
pytest-cov>=3.0
black>=22.0
pylint>=2.13
mypy>=0.950
```

#### 6.2 Update `setup.py` with Version Constraints
**Priority: HIGH**

```python
setup(
    # ... other config ...
    python_requires='>=3.8,<3.13',
    install_requires=[
        'openpyxl>=3.0,<4.0',
        'lxml>=4.9',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-cov>=3.0',
            'black>=22.0',
            'pylint>=2.13',
            'mypy>=0.950',
        ],
        'build': [
            'pyinstaller>=5.0,<7.0',
            'setuptools>=65.0',
            'wheel>=0.38',
        ],
    },
)
```

---

## 7. SECURITY: XML and File Processing

### Current Issues

```python
# ❌ Vulnerable to XML bomb attacks
tree = eTree.parse(filename)  # No protection

# ❌ Path traversal vulnerability potential
filepath = config.get("WAV_DIR", "/default")
```

### Recommendations

#### 7.1 Secure XML Parsing
**Priority: HIGH (for untrusted ELAN files)**

```python
from xml.etree import ElementTree as ET
import logging

logger = logging.getLogger(__name__)

# Disable XML entities to prevent XXE attacks
for event, elem in ET.iterparse(
    filename, 
    events=['start-ns']  # Only process namespaces, not expand entities
):
    pass

# Better approach - use defusedxml for untrusted input
try:
    from defusedxml import ElementTree as DefusedET
    tree = DefusedET.parse(filename)
except ImportError:
    logger.warning("defusedxml not installed, using standard parser")
    tree = ET.parse(filename)
```

#### 7.2 Validate and Constrain Paths
**Priority: MEDIUM**

```python
from pathlib import Path

def validate_output_path(config_path: Path, output_dir: Path) -> Path:
    """Ensure output path is within expected directory."""
    # Resolve to absolute paths
    config_dir = config_path.parent.resolve()
    output = output_dir.resolve()
    
    # Check path is within config directory (optional safety)
    if not str(output).startswith(str(config_dir.parent)):
        logger.warning(
            f"Output directory {output} outside config directory {config_dir}"
        )
    
    return output
```

---

## 8. TESTING: Add Test Coverage

### Current Issues
- No tests in project
- No way to validate changes don't break functionality
- Hard to debug issues

### Recommendations

#### 8.1 Create Test Structure
**Priority: MEDIUM**

```
tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures
├── test_config.py                 # Config loading/validation
├── test_lift.py                   # LIFT file processing
├── test_eaf.py                    # ELAN file processing
├── test_web.py                    # Web export
└── fixtures/
    ├── sample.lift
    ├── sample.eaf
    └── sample.cfg
```

#### 8.2 Example Test File
**Priority: MEDIUM**

```python
# tests/test_lift.py
import pytest
from pathlib import Path
from kwaras.formats.lift import Lift

@pytest.fixture
def sample_lift():
    """Load sample LIFT file."""
    return Lift(Path(__file__).parent / "fixtures/sample.lift")

def test_lift_loading(sample_lift):
    """Test LIFT file loads without error."""
    assert sample_lift.root is not None
    assert len(sample_lift.lexemes) > 0

def test_lift_entry_lookup(sample_lift):
    """Test GUID lookup in LIFT."""
    entry = sample_lift.getEntry("test_guid")
    assert entry is not None

def test_invalid_lift_file():
    """Test error handling for invalid LIFT."""
    with pytest.raises(FileNotFoundError):
        Lift("nonexistent.lift")
```

#### 8.3 Add Testing to CI/CD
**Priority: LOW (post-modernization)**

Create `.github/workflows/test.yml` for GitHub Actions.

---

## 9. GUI MODERNIZATION: Streamlit + Electron as the Core Path

### 9.1 Design Goal

Move to a modern, local desktop UI that is:
- built with Streamlit for fast Python-first development
- packaged with Electron for native desktop distributables
- fully compatible with existing processing logic (`convert_lexicon`, `export_corpus`, etc.)
- cross-platform (Windows/macOS/Linux) and runnable locally

### 9.2 Implementation Blueprint

#### 9.2.1 Streamlit App
- Add a Streamlit app entrypoint `kwaras_streamlit.py`
- Build workflows:
  - Lexicon conversion with LIFT file selection
  - Corpus export with config path + directory selectors
  - Status updates + progress bars
- Keep existing JSON config schema (corpus.cfg, lexicon.cfg)
- Reuse functions in `kwaras.gui` where possible

#### 9.2.2 Electron Wrapper
- Add Electron `main.js`, `package.json`, and packaging scripts
- Electron starts Streamlit server and opens a window to localhost
- Ensure graceful shutdown kills Streamlit process
- Package with `electron-builder` into `.exe`, `.dmg`, `.AppImage`

#### 9.2.3 CLI Fallback
- Keep CLI endpoints from milestone 1 to support automation:
  - `kwaras convert-lexicon --config lexicon.cfg`
  - `kwaras export-corpus --config corpus.cfg`
- Document both CLI and Streamlit usage

### 9.3 Benefits
- Streamlit requires minimal UI code and supports interactive controls
- Electron provides a desktop UX, removing browser-run burden
- UI updates with every run; no manual template/JavaScript engineering

### 9.4 Optional alternative tracks
- PySimpleGUI: useful for a pure desktop UI if Electron is unwanted
- PyQt6: good for maximum native styling and app polish
- Flask-based local web server: real web app route, less desktop feel

### 9.5 Roadmap in this section
1. Build Streamlit GUI: simple, working, local-first.
2. Wrap as Electron app to ship cross-platform executables.
3. Keep CLI commands in place for headless automation and scripting.
4. Continue to refine core processing, validation, and error handling.

---

## 10. CODE STRUCTURE: Organization Improvements

### Current Issues

```python
# gui.py has imports in functions
def convert_lexicon():
    from kwaras.conf import config      # ❌ Inefficient
    from kwaras.formats.lift import Lift
    from kwaras.process import liftadd
```

### Recommendations

#### 10.1 Top-level Module Organization
**Priority: MEDIUM**

```python
# gui.py - Top-level imports
import logging
import argparse
from pathlib import Path
from tkinter import messagebox

from kwaras.conf.config import ConfigWindow
from kwaras.formats.lift import Lift
from kwaras.process.liftadd import exposeGuid, addRarAllomorphs
from kwaras.process.web import main as export_web

logger = logging.getLogger(__name__)

def convert_lexicon() -> None:
    """Convert lexicon without local imports."""
    config_window = ConfigWindow("lexicon.cfg", parts=["EAFL"])
    # ... rest of implementation
```

#### 10.2 Separate CLI from GUI Logic
**Priority: MEDIUM**

```
kwaras/
├── cli.py          # Command-line interface
├── gui/
│   ├── __init__.py
│   ├── main.py     # GUI entry point
│   └── dialogs.py  # Dialog windows
├── lib/            # Core logic
│   ├── config.py   # Configuration
│   ├── lexicon.py  # Lexicon processing
│   └── export.py   # Export operations
└── formats/        # Format handlers
```

This separation makes testing and reuse easier.

---

## Implementation Priority (Milestone-Based)

### Milestone 1: Minimal CLI Support and Documentation (0-1 months)
- Add command-line entry points using `setuptools` `console_scripts`
- Document installation and execution in README.md (venv setup, `pip install -e .`, common commands)
- Keep existing GUI as-is, add small CLI hooks for `convert_lexicon`, `export_corpus`, `check-install`
- Validate config and handle errors cleanly from CLI

### Milestone 2: PyInstaller Executables (1-2 months)
- Migrate build pipeline from `py2exe/py2app` to PyInstaller
- Create cross-platform `pyinstaller` spec and build docs
- Generate and verify builds on Windows/macOS/Linux
- Add script: `build_pyinstaller.sh` / `build_pyinstaller.ps1`

### Milestone 3: Streamlit + Electron Executables (2-4 months)
- Implement Streamlit UI for all major flows (lexicon conversion, corpus export)
- Add electron packaging layer (main.js + package.json)
- Document how to run `streamlit run` and `npm run dist`
- Test and package desktop installers

### Milestone 4: Yunohost App from Streamlit UI (4-6 months)
- Adapt Streamlit app for Yunohost packaging and deployments
- Create Yunohost manifest and install scripts
- Ensure service startup/shutdown plus user config works
- Add Yunohost docs and release artifacts

---

## Implementation Notes

This document now maps directly to milestones:
- Milestone 1: CLI and docs (immediate)
- Milestone 2: PyInstaller builds
- Milestone 3: Streamlit + Electron executables
- Milestone 4: Yunohost app release

Each milestone includes stability checkpoints:
- code quality (type hints, logging, error management)
- tests (unit + integration)
- dependency pinning and environment setup
- release packaging and docs

### Immediate actions (Milestone 1)
- Update `setup.py` with `setuptools` and `console_scripts`
- Add concise `README` CLI install/run section
- Add `check-install` and workflow tests

### Next steps (Milestone 2)
- Add `pyinstaller` support and cross-platform script
- Validate generated binaries in CI

### Major UI transition (Milestone 3)
- Build Streamlit app from existing logic
- Add Electron packaging and distribution

### Specialty deployment (Milestone 4)
- Build Yunohost manifest + integration
- Reuse Streamlit UI in server-hosted environment

---

### Estimated Python Version Support After Modernization

| Version | Support |
|---------|---------|
| Python 3.8 | ✅ Yes (production) |
| Python 3.9 | ✅ Yes (production) |
| Python 3.10 | ✅ Yes (production) |
| Python 3.11 | ✅ Yes (production) |
| Python 3.12+ | ⏳ Planned |

---

### Benefits Summary

| Issue | Benefit |
|-------|---------|
| setuptools + PyInstaller | Python 3.12+ support, active maintenance, single cross-platform build tool |
| pathlib + context managers | Cross-platform compatibility, no resource leaks |
| Type hints | Better IDE support, easier debugging, fewer runtime errors |
| Logging | Better diagnostics, production-ready monitoring |
| Error handling | More robust, user-friendly error messages |
| Tests | Prevent regressions, easier refactoring |
| Version constraints | Reproducible builds, fewer dependency conflicts |
| Streamlit + Electron | Modern professional UI, native app distribution, minimal code changes |

---
