"""Command-line interface for Kwaras.

This module provides CLI access to Kwaras functionality without requiring a GUI.
Supports lexicon conversion, corpus export, and installation verification.

Usage:
    kwaras convert-lexicon --config lexicon.cfg
    kwaras export-corpus --config corpus.cfg
    kwaras check-install
"""

import argparse
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Optional


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI mode."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )


def load_config_safely(config_path: str) -> dict:
    """Load JSON config with proper error handling.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Parsed configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file contains invalid JSON
    """
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return {}
            return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {config_path}: {e}")


def validate_config(config: dict, required_keys: list) -> None:
    """Validate config has all required keys.
    
    Args:
        config: Configuration dictionary
        required_keys: List of required key names
        
    Raises:
        ValueError: If any required keys are missing
    """
    missing = [key for key in required_keys if key not in config]
    if missing:
        raise ValueError(f"Configuration missing required keys: {', '.join(missing)}")


def validate_dependencies() -> list:
    """Check for required dependencies.
    
    Returns:
        List of missing dependencies (empty if all present)
    """
    required_deps = ['openpyxl']
    missing = []
    for dep in required_deps:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    return missing


def convert_lexicon_cli(config_path: str = "lexicon.cfg", use_gui: bool = False) -> int:
    """Convert LIFT lexicon to EAFL format. CLI version.
    
    Args:
        config_path: Path to lexicon configuration file
        use_gui: (Unused, for API compatibility)
        
    Returns:
        0 on success, 1 on failure
    """
    # Check dependencies first
    missing = validate_dependencies()
    if missing:
        print(f"Missing required dependencies: {', '.join(missing)}", file=sys.stderr)
        print("Run: pip install -r requirements.txt", file=sys.stderr)
        return 1
    
    from kwaras.formats.lift import Lift
    from kwaras.process import liftadd
    
    logger = logging.getLogger(__name__)
    
    try:
        # Load config
        cfg = load_config_safely(config_path)
        validate_config(cfg, ['EAFL_DIR', 'LIFT'])
        
        dir_name = cfg["EAFL_DIR"]
        inf_name = cfg["LIFT"]
        
        # Validate input file
        lift_path = Path(inf_name)
        if not lift_path.exists():
            logger.error(f"LIFT file not found: {inf_name}")
            return 1
        
        if lift_path.suffix.lower() != ".lift":
            logger.error(f"Expected .lift file, got: {lift_path.suffix}")
            return 1
        
        # Process
        base = lift_path.stem
        
        logger.info(f"Exposing GUID as field in {inf_name}")
        lift = Lift(inf_name)
        lift = liftadd.exposeGuid(lift)
        
        guid_path = Path(dir_name) / f"{base}-guid.lift"
        lift.write(str(guid_path))
        logger.info(f"Written: {guid_path}")
        
        logger.info(f"Adding allomorphs to {inf_name}")
        lift = liftadd.addRarAllomorphs(lift)
        
        added_path = Path(dir_name) / f"{base}-added.lift"
        lift.write(str(added_path))
        logger.info(f"Written: {added_path}")
        
        logger.info("Converting LIFT format to EAFL format")
        eafl_path = Path(dir_name) / f"{base}-import.eafl"
        lift.toEAFL(str(eafl_path))
        logger.info(f"Written: {eafl_path}")
        
        logger.info("Lexicon conversion completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Lexicon conversion failed: {e}")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            traceback.print_exc()
        return 1


def export_corpus_cli(config_path: Optional[str] = None, use_gui: bool = False) -> int:
    """Export ELAN corpus to web interface. CLI version.
    
    Args:
        config_path: Path to corpus configuration file
        use_gui: (Unused, for API compatibility)
        
    Returns:
        0 on success, 1 on failure
    """
    # Check dependencies first
    missing = validate_dependencies()
    if missing:
        print(f"Missing required dependencies: {', '.join(missing)}", file=sys.stderr)
        print("Run: pip install -r requirements.txt", file=sys.stderr)
        return 1
    
    from kwaras.process import web
    
    logger = logging.getLogger(__name__)
    
    try:
        # Determine config path
        if config_path is None:
            corpus_cfg = load_config_safely("corpus.cfg")
            validate_config(corpus_cfg, ['LANGUAGE'])
            config_path = f"{corpus_cfg['LANGUAGE']}.cfg"
        
        cfg = load_config_safely(config_path)
        validate_config(cfg, ['FILE_DIR', 'OLD_EAFS', 'WWW'])
        
        logger.info(f"Exporting corpus from config: {config_path}")
        web.main(cfg)
        logger.info("Corpus export completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Corpus export failed: {e}")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            traceback.print_exc()
        return 1


def check_install_cli() -> int:
    """Check if kwaras package is installed correctly with all dependencies.
    
    Returns:
        0 if installed, 1 if not installed
    """
    try:
        import kwaras
    except ImportError as e:
        print(f"Kwaras package is NOT installed correctly: {e}", file=sys.stderr)
        print("Run: pip install -e .", file=sys.stderr)
        return 1
    
    # Check for required dependencies
    required_deps = ['openpyxl']
    missing_deps = []
    for dep in required_deps:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"Kwaras is installed but missing dependencies: {', '.join(missing_deps)}", file=sys.stderr)
        print("Run: pip install -r requirements.txt", file=sys.stderr)
        return 1
    
    print("Kwaras package is installed correctly.")
    print(f"Version: {getattr(kwaras, '__version__', 'unknown')}")
    return 0


def is_headless() -> bool:
    """Detect if running in headless/CLI mode.
    
    Returns:
        True if running without a display/tty
    """
    # Check for no display on Unix
    if os.name != 'nt' and not os.environ.get('DISPLAY'):
        return True
    # Check if stdout is not a tty (piped/redirected)
    if not sys.stdout.isatty():
        return True
    return False


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Kwaras - Tools for managing ELAN corpus files'
    )
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # convert-lexicon command
    lex_parser = subparsers.add_parser('convert-lexicon',
                                        help='Convert FLEx LIFT lexicon to EAFL format')
    lex_parser.add_argument('--config', '-c', default='lexicon.cfg',
                            help='Path to lexicon configuration file (default: lexicon.cfg)')
    
    # export-corpus command
    exp_parser = subparsers.add_parser('export-corpus',
                                        help='Export ELAN corpus as web interface files')
    exp_parser.add_argument('--config', '-c', default=None,
                            help='Path to corpus configuration file (default: auto-detect from corpus.cfg)')
    
    # check-install command
    subparsers.add_parser('check-install', help='Check if kwaras is installed correctly')
    
    # Legacy compatibility: direct flags (hidden)
    parser.add_argument('--convert-lexicon', action='store_true',
                        help=argparse.SUPPRESS)
    parser.add_argument('--export-corpus', action='store_true',
                        help=argparse.SUPPRESS)
    parser.add_argument('--select-action', action='store_true',
                        help=argparse.SUPPRESS)
    parser.add_argument('--config',
                        help=argparse.SUPPRESS)
    
    return parser.parse_args()


def main() -> int:
    """Main CLI entry point.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_args()
    setup_logging(args.verbose)
    
    # Handle subcommand style
    if args.command == 'convert-lexicon':
        return convert_lexicon_cli(args.config)
    elif args.command == 'export-corpus':
        return export_corpus_cli(args.config)
    elif args.command == 'check-install':
        return check_install_cli()
    
    # Handle legacy flag style (backward compatibility)
    if args.convert_lexicon:
        config = args.config if args.config else 'lexicon.cfg'
        return convert_lexicon_cli(config)
    if args.export_corpus:
        return export_corpus_cli(args.config)
    if args.select_action:
        # Launch GUI
        from kwaras.gui import main as gui_main
        return gui_main()
    
    # Default: show help
    args.parser.print_help()
    return 0


# Entry points for setuptools console_scripts
def convert_lexicon_cmd() -> None:
    """Entry point for kwaras-convert-lexicon command."""
    args = parse_args()
    setup_logging(args.verbose)
    sys.exit(convert_lexicon_cli(getattr(args, 'config', 'lexicon.cfg')))


def export_corpus_cmd() -> None:
    """Entry point for kwaras-export-corpus command."""
    args = parse_args()
    setup_logging(args.verbose)
    sys.exit(export_corpus_cli(getattr(args, 'config', None)))


def check_install_cmd() -> None:
    """Entry point for kwaras-check-install command."""
    sys.exit(check_install_cli())


if __name__ == '__main__':
    sys.exit(main())