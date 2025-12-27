"""
Tests for the execution layer (jgo.exec).
"""

import subprocess
import sys
from pathlib import Path

import pytest

from jgo.env import Environment
from jgo.env.lockfile import LockFile
from jgo.exec import JavaLocator, JavaRunner, JavaSource, JVMConfig


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

    def test_auto_java(self):
        """Test obtaining Java via auto mode."""
        locator = JavaLocator(java_source=JavaSource.AUTO, java_version=11)
        java_path = locator.locate()

        assert java_path.exists()
        version = locator._get_java_version(java_path)
        assert version == 11


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

        # Create a lockfile with the main class
        lockfile = LockFile(
            dependencies=[],
            entrypoints={"main": "org.example.HelloWorld"},
            default_entrypoint="main",
        )
        lockfile.save(env.lock_path)

        # Reload to pick up lockfile
        return Environment(env_path)

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

    def test_run_requires_main_class(self, tmp_path):
        """Test that run() requires a main class."""
        # Create environment with no main class (empty lockfile)
        env_path = tmp_path / "no_main_env"
        jars_dir = env_path / "jars"
        jars_dir.mkdir(parents=True)
        env = Environment(env_path)

        # Create a lockfile with no entrypoints
        lockfile = LockFile(dependencies=[])
        lockfile.save(env.lock_path)

        runner = JavaRunner()

        with pytest.raises(RuntimeError, match="No main class"):
            runner.run(Environment(env_path))

    def test_run_requires_jars(self, tmp_path):
        """Test that run() requires JARs in environment."""
        # Create environment with no JARs
        env_path = tmp_path / "empty_env"
        env_path.mkdir()
        env = Environment(env_path)

        # Create a lockfile with main class but no JARs
        lockfile = LockFile(
            dependencies=[],
            entrypoints={"main": "org.example.Main"},
            default_entrypoint="main",
        )
        lockfile.save(env.lock_path)

        runner = JavaRunner()

        with pytest.raises(RuntimeError, match="No JARs found"):
            runner.run(Environment(env_path))

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
        # Find the test Java source file
        test_dir = Path(__file__).parent
        java_source = test_dir / "resources" / "java" / "HelloWorld.java"
        manifest_file = test_dir / "resources" / "java" / "MANIFEST.MF"

        if not java_source.exists():
            pytest.skip("Test Java source not found")

        # Use JavaLocator to find Java consistently with how tests run
        locator = JavaLocator(java_source=JavaSource.SYSTEM)
        java_path = locator._find_java_in_path()
        if java_path is None:
            pytest.skip("Java not found")

        javac_path = java_path.parent / "javac"
        jar_path_tool = java_path.parent / "jar"
        if not javac_path.exists():
            pytest.skip(f"javac not found at {javac_path}")
        if not jar_path_tool.exists():
            pytest.skip(f"jar tool not found at {jar_path_tool}")

        # Create compilation directory
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        # Compile the Java source
        compile_result = subprocess.run(
            [str(javac_path), "-d", str(build_dir), str(java_source)],
            capture_output=True,
            text=True,
        )

        if compile_result.returncode != 0:
            pytest.skip(f"Java compilation failed: {compile_result.stderr}")

        # Create JAR file
        jar_path = tmp_path / "hello-world.jar"
        jar_result = subprocess.run(
            [
                str(jar_path_tool),
                "cfm",
                str(jar_path),
                str(manifest_file),
                "-C",
                str(build_dir),
                ".",
            ],
            capture_output=True,
            text=True,
        )

        if jar_result.returncode != 0:
            pytest.skip(f"JAR creation failed: {jar_result.stderr}")

        # Create an Environment with this JAR
        env_path = tmp_path / "env"
        env_path.mkdir()
        jars_dir = env_path / "jars"
        jars_dir.mkdir()

        # Copy JAR to environment
        import shutil

        shutil.copy(jar_path, jars_dir / "hello-world.jar")

        env = Environment(env_path)

        # Create a lockfile with the main class
        lockfile = LockFile(
            dependencies=[],
            entrypoints={"main": "org.apposed.jgo.test.HelloWorld"},
            default_entrypoint="main",
        )
        lockfile.save(env.lock_path)

        return Environment(env_path)

    def test_run_hello_world(self, hello_world_jar):
        """Test running a simple Hello World program."""
        runner = JavaRunner(java_source=JavaSource.SYSTEM)
        result = runner.run_and_capture(hello_world_jar)

        # Check that it ran successfully
        assert result.returncode == 0
        assert "Hello, World!" in result.stdout

    def test_run_with_jvm_args(self, hello_world_jar):
        """Test running with JVM arguments."""
        config = JVMConfig(system_properties={"jgo.test.property": "test_value"})
        runner = JavaRunner(jvm_config=config, java_source=JavaSource.SYSTEM)
        result = runner.run_and_capture(hello_world_jar)

        # Check that the system property was passed
        assert result.returncode == 0
        assert "System property jgo.test.property: test_value" in result.stdout

    def test_run_with_app_args(self, hello_world_jar):
        """Test running with application arguments."""
        runner = JavaRunner(java_source=JavaSource.SYSTEM)
        result = runner.run_and_capture(
            hello_world_jar, app_args=["arg1", "arg2", "arg3"]
        )

        # Check that arguments were passed
        assert result.returncode == 0
        assert "Arguments received: 3" in result.stdout
        assert "arg[0]: arg1" in result.stdout
        assert "arg[1]: arg2" in result.stdout
        assert "arg[2]: arg3" in result.stdout
