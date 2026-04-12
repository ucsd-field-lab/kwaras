"""Tests for build configuration and scripts."""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


class TestSpecFiles:
    """Tests for PyInstaller spec files."""

    def test_gui_spec_exists(self):
        """Test that gui.spec exists."""
        spec_path = PROJECT_ROOT / "gui.spec"
        assert spec_path.exists(), "gui.spec should exist"

    def test_cli_spec_exists(self):
        """Test that kwaras.spec (CLI) exists."""
        spec_path = PROJECT_ROOT / "kwaras.spec"
        assert spec_path.exists(), "kwaras.spec should exist"

    def test_gui_spec_valid_python(self):
        """Test that gui.spec is valid Python syntax."""
        spec_path = PROJECT_ROOT / "gui.spec"
        with open(spec_path, encoding="utf-8") as f:
            content = f.read()
        try:
            compile(content, str(spec_path), "exec")
        except SyntaxError as e:
            pytest.fail(f"gui.spec has syntax error: {e}")

    def test_cli_spec_valid_python(self):
        """Test that kwaras.spec is valid Python syntax."""
        spec_path = PROJECT_ROOT / "kwaras.spec"
        with open(spec_path, encoding="utf-8") as f:
            content = f.read()
        try:
            compile(content, str(spec_path), "exec")
        except SyntaxError as e:
            pytest.fail(f"kwaras.spec has syntax error: {e}")

    def test_gui_spec_has_kwaras_package(self):
        """Test that gui.spec includes kwaras package."""
        spec_path = PROJECT_ROOT / "gui.spec"
        with open(spec_path, encoding="utf-8") as f:
            content = f.read()
        assert "kwaras" in content, "gui.spec should include kwaras package"

    def test_cli_spec_has_kwaras_package(self):
        """Test that kwaras.spec includes kwaras package."""
        spec_path = PROJECT_ROOT / "kwaras.spec"
        with open(spec_path, encoding="utf-8") as f:
            content = f.read()
        assert "kwaras" in content, "kwaras.spec should include kwaras package"

    def test_specs_exclude_tkinter(self):
        """Test that spec files exclude tkinter for headless environments."""
        for spec_name in ["gui.spec", "kwaras.spec"]:
            spec_path = PROJECT_ROOT / spec_name
            with open(spec_path, encoding="utf-8") as f:
                content = f.read()
            assert "tkinter" in content, f"{spec_name} should handle tkinter"

    def test_specs_have_openpyxl_hiddenimport(self):
        """Test that spec files include openpyxl as hidden import."""
        for spec_name in ["gui.spec", "kwaras.spec"]:
            spec_path = PROJECT_ROOT / spec_name
            with open(spec_path, encoding="utf-8") as f:
                content = f.read()
            assert "openpyxl" in content, f"{spec_name} should include openpyxl"


class TestBuildScripts:
    """Tests for build scripts."""

    def test_github_workflow_exists(self):
        """Test that GitHub Actions build workflow exists."""
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "build.yml"
        assert workflow_path.exists(), "build workflow should exist"

    def test_build_ps1_exists(self):
        """Test that build.ps1 exists (Windows)."""
        build_script = PROJECT_ROOT / "build.ps1"
        assert build_script.exists(), "build.ps1 should exist"

    def test_build_sh_exists(self):
        """Test that build.sh exists (Unix)."""
        build_script = PROJECT_ROOT / "build.sh"
        assert build_script.exists(), "build.sh should exist"

    def test_build_sh_is_executable(self):
        """Test that build.sh exists (permissions handled in CI/build)."""
        build_script = PROJECT_ROOT / "build.sh"
        assert build_script.exists(), "build.sh should exist"


class TestWorkflow:
    """Tests for GitHub Actions workflow."""

    def test_workflow_has_build_jobs(self):
        """Test workflow defines test and build jobs."""
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "build.yml"
        with open(workflow_path, encoding="utf-8") as f:
            content = f.read()
        assert "test:" in content
        assert "build-windows:" in content
        assert "build-unix:" in content


class TestRequirements:
    """Tests for requirements.txt."""

    def test_pyinstaller_in_requirements(self):
        """Test that pyinstaller is in requirements.txt."""
        req_path = PROJECT_ROOT / "requirements.txt"
        with open(req_path, encoding="utf-8") as f:
            content = f.read()
        assert "pyinstaller" in content.lower(), "requirements.txt should include pyinstaller"
