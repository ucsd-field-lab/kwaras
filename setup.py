"""Modern setuptools configuration for Kwaras."""

from pathlib import Path

from setuptools import find_packages, setup

VERSION = "3.0.0rc3"


def collect_web_files():
    """Collect all web static files for packaging."""
    web_files = []
    web_dir = Path("web")
    if web_dir.exists():
        for pattern in ["*.html", "css/**/*.css", "css/**/*.png", "js/**/*.js"]:
            for f in web_dir.rglob(pattern):
                rel_path = f.relative_to(web_dir)
                web_files.append((f"web/{rel_path.parent}", [str(f)]))
    return web_files


setup(
    name="kwaras",
    version=VERSION,
    author="Lucien Carroll",
    author_email="lucien@discurs.us",
    description="Tools for managing ELAN corpus files",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="http://github.com/ucsd-field-lab/kwaras",
    license="MIT",

    # Modern package discovery using find_packages
    packages=find_packages(include=["kwaras", "kwaras.*"]),

    # Python version support
    python_requires=">=3.8,<3.13",

    # Production dependencies with version constraints
    install_requires=[
        "openpyxl>=3.0,<4.0",
    ],

    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
        ],
        "build": [
            "pyinstaller>=5.0,<7.0",
        ],
    },

    # CLI entry points using console_scripts
    entry_points={
        "console_scripts": [
            "kwaras=kwaras.cli:main",
            "kwaras-convert-lexicon=kwaras.cli:convert_lexicon_cmd",
            "kwaras-export-corpus=kwaras.cli:export_corpus_cmd",
            "kwaras-check-install=kwaras.cli:check_install_cmd",
        ],
    },

    # Include package data (web static files)
    package_data={
        "kwaras": [
            "web/**/*",
        ],
    },

    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Linguistics",
    ],

    project_urls={
        "Source": "http://github.com/ucsd-field-lab/kwaras",
        "Tracker": "http://github.com/ucsd-field-lab/kwaras/issues",
    },
)
