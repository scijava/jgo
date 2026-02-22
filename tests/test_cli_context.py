from unittest.mock import MagicMock

from jgo.cli._args import (
    PLATFORM_ALIASES,
    PLATFORMS,
    build_parsed_args,
    detect_os_properties,
    expand_platform,
)
from jgo.cli._context import create_maven_context
from jgo.maven._resolver import PythonResolver


def test_create_maven_context_python_resolver_constraints():
    args = MagicMock()
    args.resolver = "python"
    args.java_version = 11
    args.os_name = "Windows XP"
    args.os_family = "Windows"
    args.os_arch = "x86"
    args.os_version = "5.1"
    args.properties = {"foo": "bar"}
    args.repo_cache = None
    args.repositories = {}

    config = {}

    context = create_maven_context(args, config)

    assert isinstance(context.resolver, PythonResolver)
    constraints = context.resolver.profile_constraints
    assert constraints.jdk == "11"
    assert constraints.os_name == "Windows XP"
    assert constraints.os_family == "Windows"
    assert constraints.os_arch == "x86"
    assert constraints.os_version == "5.1"
    assert constraints.properties == {"foo": "bar"}


def test_create_maven_context_auto_resolver_constraints():
    args = MagicMock()
    args.resolver = "auto"
    args.java_version = 17
    args.os_name = "Linux"
    args.os_family = None
    args.os_arch = None
    args.os_version = None
    args.properties = {}
    args.repo_cache = None
    args.repositories = {}

    config = {}

    context = create_maven_context(args, config)

    # Auto defaults to PythonResolver
    assert isinstance(context.resolver, PythonResolver)
    constraints = context.resolver.profile_constraints
    assert constraints.jdk == "17"
    assert constraints.os_name == "Linux"
    assert constraints.os_family is None


# Platform expansion tests


def test_expand_platform_linux_x64():
    os_name, os_family, os_arch = expand_platform("linux-x64")
    assert os_name == "Linux"
    assert os_family == "unix"
    assert os_arch == "amd64"


def test_expand_platform_linux_arm64():
    os_name, os_family, os_arch = expand_platform("linux-arm64")
    assert os_name == "Linux"
    assert os_family == "unix"
    assert os_arch == "aarch64"


def test_expand_platform_macos_x64():
    os_name, os_family, os_arch = expand_platform("macos-x64")
    assert os_name == "Mac OS X"
    assert os_family == "mac"
    assert os_arch == "x86_64"


def test_expand_platform_macos_arm64():
    os_name, os_family, os_arch = expand_platform("macos-arm64")
    assert os_name == "Mac OS X"
    assert os_family == "mac"
    assert os_arch == "aarch64"


def test_expand_platform_windows_x64():
    os_name, os_family, os_arch = expand_platform("windows-x64")
    assert os_name == "Windows"
    assert os_family == "windows"
    assert os_arch == "amd64"


def test_expand_platform_windows_arm64():
    os_name, os_family, os_arch = expand_platform("windows-arm64")
    assert os_name == "Windows"
    assert os_family == "windows"
    assert os_arch == "aarch64"


def test_expand_platform_alias_win64():
    os_name, os_family, os_arch = expand_platform("win64")
    assert os_name == "Windows"
    assert os_family == "windows"
    assert os_arch == "amd64"


def test_expand_platform_alias_macos64():
    os_name, os_family, os_arch = expand_platform("macos64")
    assert os_name == "Mac OS X"
    assert os_family == "mac"
    assert os_arch == "x86_64"


def test_expand_platform_none():
    os_name, os_family, os_arch = expand_platform(None)
    assert os_name is None
    assert os_family is None
    assert os_arch is None


def test_expand_platform_unknown():
    os_name, os_family, os_arch = expand_platform("unknown-platform")
    assert os_name is None
    assert os_family is None
    assert os_arch is None


def test_platforms_dict_complete():
    """Verify all expected platforms are defined."""
    expected_platforms = [
        "windows-x64",
        "windows-arm64",
        "macos-x64",
        "macos-arm64",
        "linux-x64",
        "linux-arm64",
    ]
    for platform in expected_platforms:
        assert platform in PLATFORMS, f"Missing platform: {platform}"


def test_platform_aliases_resolve():
    """Verify all aliases map to valid platforms."""
    for alias, platform in PLATFORM_ALIASES.items():
        assert platform in PLATFORMS, (
            f"Alias '{alias}' maps to unknown platform '{platform}'"
        )


# Auto-detection tests


def test_expand_platform_os_only():
    """OS-only platforms (e.g., 'linux') should auto-detect architecture."""
    os_name, os_family, os_arch = expand_platform("linux")
    assert os_name == "Linux"
    assert os_family == "unix"
    assert os_arch == "auto"


def test_build_parsed_args_partial_os_arch_only():
    """Specifying only --os-arch should auto-fill os_name and os_family."""
    opts = {
        "os_arch": "i386",
        "os_name": None,
        "os_family": None,
        "platform": None,
        "os_version": None,
        "properties": [],
        "repository": [],
    }
    args = build_parsed_args(opts)

    # Arch should be the specified value
    assert args.os_arch == "i386"

    # Name and family should be auto-detected from current system
    detected_name, detected_family, _ = detect_os_properties()
    assert args.os_name == detected_name
    assert args.os_family == detected_family


def test_build_parsed_args_partial_os_name_only():
    """Specifying only --os-name should auto-fill os_family and os_arch."""
    opts = {
        "os_name": "Windows",
        "os_family": None,
        "os_arch": None,
        "platform": None,
        "os_version": None,
        "properties": [],
        "repository": [],
    }
    args = build_parsed_args(opts)

    # Name should be the specified value
    assert args.os_name == "Windows"

    # Family and arch should be auto-detected from current system
    _, detected_family, detected_arch = detect_os_properties()
    assert args.os_family == detected_family
    assert args.os_arch == detected_arch


def test_build_parsed_args_no_platform_flags():
    """With no platform flags, all values should be auto-detected."""
    opts = {
        "os_name": None,
        "os_family": None,
        "os_arch": None,
        "platform": None,
        "os_version": None,
        "properties": [],
        "repository": [],
    }
    args = build_parsed_args(opts)

    # All should be auto-detected from current system
    detected_name, detected_family, detected_arch = detect_os_properties()
    assert args.os_name == detected_name
    assert args.os_family == detected_family
    assert args.os_arch == detected_arch


def test_build_parsed_args_platform_linux_auto_arch():
    """--platform linux should use concrete name/family, auto-detect arch."""
    opts = {
        "platform": "linux",
        "os_name": None,
        "os_family": None,
        "os_arch": None,
        "os_version": None,
        "properties": [],
        "repository": [],
    }
    args = build_parsed_args(opts)

    # Name and family should be from platform
    assert args.os_name == "Linux"
    assert args.os_family == "unix"

    # Arch should be auto-detected
    _, _, detected_arch = detect_os_properties()
    assert args.os_arch == detected_arch


def test_build_parsed_args_explicit_override_no_auto():
    """Explicit values should not be auto-detected/overridden."""
    opts = {
        "platform": "linux-x64",
        "os_name": None,
        "os_family": None,
        "os_arch": None,
        "os_version": None,
        "properties": [],
        "repository": [],
    }
    args = build_parsed_args(opts)

    # All should be from platform, no auto-detection needed
    assert args.os_name == "Linux"
    assert args.os_family == "unix"
    assert args.os_arch == "amd64"


def test_build_parsed_args_explicit_auto_keyword():
    """Explicit 'auto' value should trigger auto-detection."""
    opts = {
        "os_name": "auto",
        "os_family": "auto",
        "os_arch": "auto",
        "platform": None,
        "os_version": None,
        "properties": [],
        "repository": [],
    }
    args = build_parsed_args(opts)

    # All should be auto-detected
    detected_name, detected_family, detected_arch = detect_os_properties()
    assert args.os_name == detected_name
    assert args.os_family == detected_family
    assert args.os_arch == detected_arch


def test_build_parsed_args_mixed_auto_and_explicit():
    """Mix of 'auto' and explicit values should work correctly."""
    opts = {
        "os_name": "Windows",
        "os_family": "auto",  # Should be auto-detected
        "os_arch": "x86",
        "platform": None,
        "os_version": None,
        "properties": [],
        "repository": [],
    }
    args = build_parsed_args(opts)

    # Name and arch should be explicit values
    assert args.os_name == "Windows"
    assert args.os_arch == "x86"

    # Family should be auto-detected
    _, detected_family, _ = detect_os_properties()
    assert args.os_family == detected_family


def test_build_parsed_args_platform_override_with_auto():
    """Explicit 'auto' should override platform value."""
    opts = {
        "platform": "windows-x64",  # Would give Windows, windows, amd64
        "os_name": None,
        "os_family": None,
        "os_arch": "auto",  # Override arch with auto-detection
        "os_version": None,
        "properties": [],
        "repository": [],
    }
    args = build_parsed_args(opts)

    # Name and family from platform
    assert args.os_name == "Windows"
    assert args.os_family == "windows"

    # Arch should be auto-detected (overriding platform's amd64)
    _, _, detected_arch = detect_os_properties()
    assert args.os_arch == detected_arch
