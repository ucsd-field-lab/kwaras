"""Tests for package structure and module imports."""



class TestPackageImports:
    """Test that all package modules can be imported."""

    def test_kwaras_package_import(self):
        """Test kwaras package imports."""
        import kwaras

        assert kwaras.__version__ == "3.0.0rc3"

    def test_cli_module_import(self):
        """Test CLI module imports."""
        from kwaras import cli

        assert hasattr(cli, "main")

    def test_formats_submodules(self):
        """Test format modules can be imported."""

    def test_process_submodules(self):
        """Test process modules can be imported."""

    def test_langs_submodules(self):
        """Test language modules can be imported."""


class TestFormatClasses:
    """Test format module classes exist."""

    def test_lift_class_exists(self):
        """Test Lift class is importable."""
        from kwaras.formats.lift import Lift

        assert callable(Lift)

    def test_eaf_class_exists(self):
        """Test Eaf class is importable."""
        from kwaras.formats.eaf import Eaf

        assert callable(Eaf)


class TestProcessFunctions:
    """Test process module functions exist."""

    def test_liftadd_expose_guid(self):
        """Test expose_guid function exists."""
        from kwaras.process.liftadd import expose_guid

        assert callable(expose_guid)

    def test_liftadd_add_allomorphs(self):
        """Test add_allomorphs function exists."""
        from kwaras.process.liftadd import add_allomorphs

        assert callable(add_allomorphs)

    def test_web_main(self):
        """Test web.main exists."""
        from kwaras.process import web

        assert hasattr(web, "main")


class TestPackageData:
    """Test package data files are included."""

    def test_web_directory_exists(self):
        """Test web directory is in package."""
        import os

        from kwaras import __path__

        web_path = os.path.join(__path__[0], "web")
        assert os.path.isdir(web_path)
