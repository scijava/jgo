#!/usr/bin/env python
"""
Demo script showing how to use the jgo Execution Layer.

This demonstrates using JVMConfig, JavaSource, and JavaRunner
to execute Java programs from materialized environments.
"""

from pathlib import Path
from jgo.exec import JVMConfig, JavaSource, JavaRunner
from jgo.env import Environment, EnvironmentBuilder
from jgo.maven import MavenContext


def demo_basic_execution():
    """Demo: Basic execution with default configuration."""
    print("\n=== Demo: Basic Execution ===")

    # Create Maven context
    maven = MavenContext()

    # Build environment for a simple Java application
    # (Using Jython as example - it has a main class)
    builder = EnvironmentBuilder(context=maven)

    print("Building environment for org.python:jython-standalone...")
    environment = builder.from_endpoint(
        "org.python:jython-standalone:2.7.3", update=False
    )

    print(f"Environment path: {environment.path}")
    print(f"Main class: {environment.main_class}")
    print(f"JARs in classpath: {len(environment.classpath)}")

    # Run with default configuration
    runner = JavaRunner()
    print("\nRunning with default JVM configuration...")
    print("Command would execute: java [JVM args] -cp [classpath] [main class] --version")

    # Note: Uncomment to actually run
    # result = runner.run(environment, app_args=["--version"])
    # print(f"Exit code: {result.returncode}")


def demo_custom_jvm_config():
    """Demo: Custom JVM configuration."""
    print("\n=== Demo: Custom JVM Configuration ===")

    # Create custom JVM configuration
    config = JVMConfig(
        max_heap="1G",
        min_heap="256M",
        gc_options=["-XX:+UseG1GC", "-XX:MaxGCPauseMillis=200"],
        system_properties={"java.awt.headless": "true", "user.language": "en"},
        extra_args=["-verbose:gc"],
    )

    # Show generated JVM arguments
    jvm_args = config.to_jvm_args()
    print("Generated JVM arguments:")
    for arg in jvm_args:
        print(f"  {arg}")

    # Create runner with this config
    runner = JavaRunner(jvm_config=config, verbose=True)
    print(f"\nRunner configured with java_source={runner.java_source.value}")


def demo_java_source_selection():
    """Demo: Different Java source strategies."""
    print("\n=== Demo: Java Source Selection ===")

    # Strategy 1: Use system Java
    print("\n1. SYSTEM: Use system Java from PATH/JAVA_HOME")
    runner_system = JavaRunner(java_source=JavaSource.SYSTEM, verbose=True)
    print(f"   Strategy: {runner_system.java_source.value}")

    # Strategy 2: Use cjdk
    print("\n2. CJDK: Use cjdk for automatic Java management")
    print("   Note: Requires 'pip install jgo[cjdk]'")
    # runner_cjdk = JavaRunner(
    #     java_source=JavaSource.CJDK,
    #     java_version=17,
    #     java_vendor="zulu"  # Default is "zulu" (widest version support)
    # )


def demo_bytecode_detection():
    """Demo: Automatic Java version detection from bytecode."""
    print("\n=== Demo: Bytecode Version Detection ===")

    maven = MavenContext()
    builder = EnvironmentBuilder(context=maven)

    print("\nBuilding environment to detect Java version...")
    # Use a known library (you can substitute with any Maven coordinate)
    environment = builder.from_endpoint("org.python:jython-standalone:2.7.3")

    # Detect minimum Java version from bytecode
    min_java = environment.min_java_version
    print(f"Detected minimum Java version: {min_java}")
    print("This was determined by scanning .class files in the JARs")

    # Runner will automatically use this detected version
    runner = JavaRunner(java_source=JavaSource.CJDK)
    print(
        f"\nRunner will automatically ensure Java {min_java}+ is available when executing"
    )


def demo_fluent_jvm_config():
    """Demo: Fluent API for JVM configuration."""
    print("\n=== Demo: Fluent JVM Configuration ===")

    # Start with base config
    config = JVMConfig(max_heap="2G")

    # Add properties and args fluently
    config = (
        config.with_system_property("app.name", "MyApp")
        .with_system_property("app.env", "production")
        .with_extra_arg("-verbose:class")
        .with_extra_arg("-XX:+PrintCommandLineFlags")
    )

    print("Built JVM configuration fluently:")
    for arg in config.to_jvm_args():
        print(f"  {arg}")


def main():
    """Run all demos."""
    print("=" * 70)
    print("JGO 2.0 Execution Layer Demo")
    print("=" * 70)

    try:
        demo_custom_jvm_config()
        demo_java_source_selection()
        demo_fluent_jvm_config()

        # These demos require Maven resolution and can be slower
        # Uncomment to run:
        # demo_basic_execution()
        # demo_bytecode_detection()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
