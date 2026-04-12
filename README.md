# Kwaras — Tools for ELAN Corpus Management

Kwaras is a Python-based toolkit for managing linguistic corpus data in ELAN (EUDICO Linguistic Annotator) format. It provides tools to convert LIFT lexicon files, process ELAN corpora, create interactive web interfaces for corpus exploration, and align audio clips with linguistic annotations.

**Version:** 3.0.0rc3 
**License:** MIT  
**Author:** Lucien Carroll  
**Repository:** http://github.com/ucsd-field-lab/kwaras

## Overview

Kwaras simplifies the workflow for linguists and language researchers working with ELAN corpora by automating several key tasks:

- **Corpus Export**: Generate interactive HTML web interfaces from ELAN corpus exports with full-text search and filtering
- **Lexicon Management**: Convert FLEx LIFT lexicon files to ELAN-compatible EAFL format with automatic allomorph extraction
- **Audio Alignment**: Automatically find and extract sound clips from large recordings, creating annotation files for ELAN import
- **Bulk Editing**: Apply bulk modifications to ELAN corpus files with language-specific processors

## Installation

### Prerequisites

- Python 3.8 - 3.12
- pip package manager
- uv python version manager (recommended; py/pyenv are fine too)

### Standard Installation (CLI)

```bash
# Clone the repository
git clone https://github.com/ucsd-field-lab/kwaras.git
cd kwaras

# Create and activate virtual environment 
# (Windows CMD)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv venv -p 3.11
.venv/Scripts/activate
# (macOS/Linux/Git Bash/WSL)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv -p 3.11
source .venv/bin/activate

# Install dependencies and package
uv pip install -r requirements.txt
uv pip install -e .

# Verify installation
kwaras check-install
```

### CLI Usage

```bash

# Export ELAN corpus to web interface
kwaras export-corpus --config MyLanguage.cfg

# Convert LIFT lexicon to EAFL format
kwaras convert-lexicon --config lexicon.cfg

# Check installation
kwaras check-install

# Get help
kwaras --help
kwaras convert-lexicon --help
```

### GUI Usage (Legacy)

The Tkinter GUI is still available:

```bash
uv run gui.py  # export corpus
python gui.py  # equivalent, if venv is set up correctly
python gui.py --select-action
python gui.py --convert-lexicon
python gui.py --export-corpus
```

## File Inventory

### Root Level Configuration & Scripts

| File | Purpose |
|------|---------|
| `gui.py` | Main GUI application entry point; provides menu interface for corpus operations |
| `lexicon.py` | Standalone script for converting LIFT lexicon files to EAFL format |
| `setup.py` | Python setuptools configuration for building executable applications |
| `check-install.py` | Verification script to check if kwaras package is properly installed |
| `corpus.cfg` | Main configuration file template for corpus export operations |
| `Mixtec.cfg`, `Other.cfg`, `Raramuri.cfg` | Language-specific configuration files with export settings |
| `requirements.txt` | Python package dependencies (openpyxl for Excel support) |
| `MIT-LICENSE` | Project license file |
| `convert-lexicon.BAT` / `.COMMAND` | Batch scripts for Windows and macOS lexicon conversion |
| `export-corpus.BAT` / `.COMMAND` | Batch scripts for Windows and macOS corpus export |
| `install-macos.COMMAND` | macOS installation script |

### Core Package: `kwaras/`

The main Python package containing all functional modules.

#### `kwaras/conf/` — Configuration Management

| File | Purpose |
|------|---------|
| `config.py` | GUI configuration window for interactive settings; generates JSON config files |
| `rar_win.py` | Platform-specific configuration for Raramuri language on Windows |

#### `kwaras/formats/` — File Format Processors

These modules handle reading, writing, and converting between different linguistic file formats:

| File | Purpose |
|------|---------|
| `eaf.py` | ELAN Analysis Format processor; parses and modifies ELAN XML corpus files |
| `lift.py` | LIFT (Lexical Interchange Format) processor; reads and converts FLEx lexicon data |
| `textgrid.py` | Praat TextGrid format support for time-aligned annotations |
| `utfcsv.py` | UTF-8 CSV format handler for corpus data import/export |
| `xlsx.py` | Excel XLSX format handler for spreadsheet-based corpus data |

#### `kwaras/langs/` — Language-Specific Processors

These modules contain language-specific rules for data processing and bulk edits:

| File | Purpose |
|------|---------|
| `Gitonga.py` | Gi'tonga language processor |
| `Kumiai.py` | Kumiai language processor |
| `Mixtec.py` | Mixtec language processor |
| `Raramuri.py` | Raramuri (Tarahumara) language processor |
| `Other.py` | Generic language processor for undefined languages |

#### `kwaras/process/` — Data Processing Tools

| File | Purpose |
|------|---------|
| `web.py` | Converts ELAN corpus exports to interactive HTML web interface with jQuery DataTables |
| `timealign.py` | Extracts sound clips from large audio files; creates CSV annotation files for ELAN import |
| `liftadd.py` | Lexicon processing utility; exposes GUIDs and adds allomorphs to LIFT files |
| `reparse.py` | Generic text parsing and reprocessing utilities |

### Web Interface Resources: `web/`

Pre-built web interface components for interactive corpus exploration:

| Directory/File | Purpose |
|---|---|
| `index_wrapper.html` | Template for corpus web interface |
| `index.html`, `clip_metadata.html` | Generated corpus web pages |
| `clip_metadata.csv` | Metadata for corpus clips |
| `clips/` | Directory containing extracted audio clips |
| `css/` | Stylesheets including jQuery DataTables themes |
| `js/` | JavaScript libraries (jQuery, DataTables, ColVis, TableTools plugins) |
| `css/smoothness/` | jQuery UI theme files and images |

After export, the output `www/` directory will be a copy of `web/` plus additional files:

| Directory/File | Purpose |
|---|---|
| `index.html`| Generated corpus web page |
| `clip_metadata.csv`, `clip_metadata.html` | Metadata for corpus clips |
| `clips/` | Directory containing extracted audio clips |


## Configuration

Kwaras uses JSON configuration files to specify corpus and export settings.

### Corpus Export Configuration (`corpus.cfg`)

Main config with language selection:

```json
{
   "LANGUAGE": "Other"
}
```

### Language-Specific Configuration (`Other.cfg`, etc.)

Detailed export settings:

```json
{
   "LANGUAGE": "Other",
   "FILE_DIR": "",
   "EXP_FIELDS": "Phonetic, Spanish, English, Note",
   "OLD_EAFS": "C:\\Users\\serap\\Documents\\corpus-data-versions",
   "META": "C:\\Users\\serap\\Documents\\metadata.csv",
   "WAV": "C:\\Users\\serap\\Documents\\wav",
   "WWW": "C:\\Users\\serap\\Documents\\www",
   "PG_TITLE": "Kwaras Corpus",
   "NAV_BAR": "<div align=\"right\">...</div>"
}
```

**Configuration sections:**
- **MAIN**: Basic settings (language, directories)
- **CSV**: CSV export options (fields, formatting)
- **HTML**: Web interface appearance and navigation

The GUI provides interactive windows to configure each section.

## Workflow Examples

### Exporting a Corpus to Web Interface

1. Run `python gui.py`
2. Select language and configure export settings
3. Specify directories for:
   - ELAN files (`OLD_EAFS`)
   - Metadata CSV (`META`)
   - Audio files (`WAV`)
   - Output location (`WWW`)
4. Tool generates interactive HTML interface in output directory:
   - `index.html` — Main searchable corpus table
   - `clips/` — Directory with extracted audio clips
   - `clip_metadata.csv` — Full clip metadata
   - `css/` and `js/` — Styling and interactivity may need to be copied manually from `web/` directory

## Troubleshooting

**"Package not installed" error:**
- Ensure kwaras is installed: `pip install -e .`
- Or run: `python setup.py install`

**Missing configuration files:**
- Create them interactively through the GUI config windows
- Or copy and edit example `.cfg` files provided

**Web interface not displaying correctly:**
- Verify all files in `web/` directory are present
- Check that CSS and JS files are accessible
- See web interface HTML files for loading paths

**Audio clips not found:**
- Ensure `WAV` directory in config points to exported audio files
- Verify `OLD_EAFS` directory contains ELAN export files
- Check that filenames match between ELAN exports and WAV files

## Building from Source

Kwaras can be built as standalone executables using PyInstaller.

### Executables

Kwaras provides two pre-built executables:

| Executable | Purpose | Usage |
|------------|---------|-------|
| `gui` / `gui.exe` | GUI application | Launch for interactive corpus management |
| `kwaras` / `kwaras.exe` | CLI application | Run `kwaras --help` for available commands |

#### CLI Commands

```bash
# Export ELAN corpus to web interface
kwaras export-corpus --config MyLanguage.cfg

# Convert LIFT lexicon to EAFL format
kwaras convert-lexicon --config lexicon.cfg

# Check installation
kwaras check-install

# Get help
kwaras --help
```

### Prerequisites

- Python 3.8-3.12
- pyinstaller: `pip install pyinstaller`

### Building

#### Windows

```powershell
# Build both GUI and CLI executables
.\build.ps1

# Build specific target
.\build.ps1 -Target gui    # GUI only
.\build.ps1 -Target cli   # CLI only

# Clean and rebuild
.\build.ps1 -Clean
```

#### macOS/Linux

```bash
# Make script executable
chmod +x build.sh

# Build both GUI and CLI executables
./build.sh

# Build specific target
./build.sh gui    # GUI only
./build.sh cli   # CLI only

# Clean and rebuild
./build.sh --clean
```

### Build Output

Executables are created in the `dist/` directory:

- `dist/gui` — GUI application (Windows: `gui.exe`)
- `dist/kwaras` — CLI application (Windows: `kwaras.exe`)

### Spec Files

The build uses PyInstaller spec files:

| File | Purpose |
|------|---------|
| `gui.spec` | GUI executable build configuration (Windows) |
| `kwaras.spec` | CLI executable build configuration (Windows) |
| `build.sh` | Unix build script (generates spec files dynamically) |

### Testing Build

```bash
# Verify GUI executable
./dist/gui.exe --help

# Verify CLI executable
./dist/kwaras.exe --help
```


