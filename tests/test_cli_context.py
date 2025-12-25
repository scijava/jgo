from unittest.mock import MagicMock

from jgo.cli.context import create_maven_context
from jgo.cli.parser import PLATFORM_ALIASES, PLATFORMS, expand_platform
from jgo.maven.resolver import PythonResolver


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
