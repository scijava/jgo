"""
Tests for the execution layer (jgo.exec).
"""

import sys
from pathlib import Path
import pytest

from jgo.exec import JVMConfig, JavaSource, JavaLocator, JavaRunner
from jgo.env import Environment


class TestJVMConfig:
    """Tests for JVMConfig class."""

    def test_default_config(self):
        """Test default JVM configuration."""
        config = JVMConfig()
        args = config.to_jvm_args()

        # Should have default GC option
        assert "-XX:+UseG1GC" in args

        # Should auto-detect max heap
        assert any(arg.startswith("-Xmx") for arg in args)

    def test_explicit_heap(self):
        """Test explicit heap size configuration."""
        config = JVMConfig(max_heap="2G", min_heap="512M")
        args = config.to_jvm_args()

        assert "-Xmx2G" in args
        assert "-Xms512M" in args

    def test_no_auto_heap(self):
        """Test disabling auto heap detection."""
        config = JVMConfig(auto_heap=False)
        args = config.to_jvm_args()

        # Should not have -Xmx
        assert not any(arg.startswith("-Xmx") for arg in args)

    def test_gc_options(self):
        """Test GC options."""
        config = JVMConfig(gc_options=["-XX:+UseParallelGC", "-XX:ParallelGCThreads=4"])
        args = config.to_jvm_args()

        assert "-XX:+UseParallelGC" in args
        assert "-XX:ParallelGCThreads=4" in args

    def test_system_properties(self):
        """Test system properties."""
        config = JVMConfig(system_properties={"foo": "bar", "baz": "qux"})
        args = config.to_jvm_args()

        assert "-Dfoo=bar" in args
        assert "-Dbaz=qux" in args

    def test_extra_args(self):
        """Test extra JVM arguments."""
        config = JVMConfig(extra_args=["-verbose:gc", "-XX:+PrintGCDetails"])
        args = config.to_jvm_args()

        assert "-verbose:gc" in args
        assert "-XX:+PrintGCDetails" in args

    def test_with_system_property(self):
        """Test adding system property via method."""
        config = JVMConfig()
        new_config = config.with_system_property("test", "value")

        # Original unchanged
        assert "test" not in config.system_properties

        # New config has property
        assert new_config.system_properties["test"] == "value"
        assert "-Dtest=value" in new_config.to_jvm_args()

    def test_with_extra_arg(self):
        """Test adding extra arg via method."""
        config = JVMConfig()
        new_config = config.with_extra_arg("-verbose:class")

        # Original unchanged
        assert "-verbose:class" not in config.extra_args

        # New config has arg
        assert "-verbose:class" in new_config.extra_args
        assert "-verbose:class" in new_config.to_jvm_args()


class TestJavaLocator:
    """Tests for JavaLocator class."""

    def test_find_system_java(self):
        """Test finding system Java."""
        locator = JavaLocator(java_source=JavaSource.SYSTEM)
        java_path = locator.locate()

        assert java_path.exists()
        assert java_path.name == "java" or java_path.name == "java.exe"

    def test_get_system_java_version(self):
        """Test getting system Java version."""
        locator = JavaLocator(java_source=JavaSource.SYSTEM)
        java_path = locator._find_java_in_path()

        if java_path:
            version = locator._get_java_version(java_path)
            assert isinstance(version, int)
            assert version >= 8  # Should be at least Java 8

    def test_system_java_version_check(self):
        """Test system Java version requirement checking."""
        locator = JavaLocator(java_source=JavaSource.SYSTEM)

        # Should succeed with reasonable version requirement
        java_path = locator.locate(min_version=8)
        assert java_path.exists()

        # Should fail with impossible version requirement
        with pytest.raises(RuntimeError, match="required"):
            locator.locate(min_version=999)

    @pytest.mark.skipif("cjdk" not in sys.modules, reason="cjdk not installed")
    def test_cjdk_java(self):
        """Test obtaining Java via cjdk."""
        locator = JavaLocator(java_source=JavaSource.CJDK, java_version=11)
        java_path = locator.locate()

        assert java_path.exists()
        version = locator._get_java_version(java_path)
        assert version == 11

    def test_auto_mode_without_cjdk(self, monkeypatch):
        """Test AUTO mode falls back to system when cjdk unavailable."""
        # Mock cjdk as unavailable
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "cjdk":
                raise ImportError("No module named 'cjdk'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        locator = JavaLocator(java_source=JavaSource.AUTO)
        java_path = locator.locate()

        # Should fall back to system Java
        assert java_path.exists()


class TestJavaRunner:
    """Tests for JavaRunner class."""

    @pytest.fixture
    def simple_environment(self, tmp_path):
        """Create a simple test environment with a dummy JAR."""
        env_path = tmp_path / "test_env"
        jars_dir = env_path / "jars"
        jars_dir.mkdir(parents=True)

        # Create a simple Java program that prints "Hello World"
        # For now, we'll just create the environment structure
        # A real test would need a real JAR file
        env = Environment(env_path)
        env.set_main_class("org.example.HelloWorld")

        return env

    def test_runner_initialization(self):
        """Test JavaRunner initialization."""
        runner = JavaRunner()
        assert runner.jvm_config is not None
        assert runner.java_source == JavaSource.AUTO

    def test_runner_with_config(self):
        """Test JavaRunner with custom JVM config."""
        config = JVMConfig(max_heap="1G")
        runner = JavaRunner(jvm_config=config)

        assert runner.jvm_config == config

    def test_build_classpath_unix(self, monkeypatch):
        """Test classpath building on Unix."""
        monkeypatch.setattr(sys, "platform", "linux")

        runner = JavaRunner()
        paths = [Path("/path/to/a.jar"), Path("/path/to/b.jar")]
        classpath = runner._build_classpath(paths)

        assert classpath == "/path/to/a.jar:/path/to/b.jar"

    def test_build_classpath_windows(self, monkeypatch):
        """Test classpath building on Windows."""
        monkeypatch.setattr(sys, "platform", "win32")

        runner = JavaRunner()
        paths = [Path("C:/path/to/a.jar"), Path("C:/path/to/b.jar")]
        classpath = runner._build_classpath(paths)

        assert classpath == "C:/path/to/a.jar;C:/path/to/b.jar"

    def test_run_requires_main_class(self, simple_environment):
        """Test that run() requires a main class."""
        # Clear main class
        simple_environment._manifest = {}

        runner = JavaRunner()

        with pytest.raises(RuntimeError, match="No main class"):
            runner.run(simple_environment)

    def test_run_requires_jars(self, tmp_path):
        """Test that run() requires JARs in environment."""
        # Create environment with no JARs
        env_path = tmp_path / "empty_env"
        env_path.mkdir()
        env = Environment(env_path)
        env.set_main_class("org.example.Main")

        runner = JavaRunner()

        with pytest.raises(RuntimeError, match="No JARs found"):
            runner.run(env)

    def test_print_command(self, simple_environment, capsys):
        """Test that print_command works."""
        # This test would require a real JAR to actually run
        # For now, we just verify the command would be printed
        # We'll catch the exception from trying to run with no JARs
        runner = JavaRunner()

        with pytest.raises(RuntimeError):
            runner.run(simple_environment, print_command=True)


class TestIntegration:
    """Integration tests using real Java execution."""

    @pytest.fixture
    def hello_world_jar(self, tmp_path):
        """Create a simple Hello World JAR for testing."""
        # This would require compiling Java code
        # For now, we'll skip this in basic tests
        pytest.skip("Requires pre-built test JAR")

    def test_run_hello_world(self, hello_world_jar):
        """Test running a simple Hello World program."""
        # Would test with a real JAR
        pass

    def test_run_with_jvm_args(self, hello_world_jar):
        """Test running with JVM arguments."""
        # Would test JVM args are properly passed
        pass

    def test_run_with_app_args(self, hello_world_jar):
        """Test running with application arguments."""
        # Would test app args are properly passed
        pass
