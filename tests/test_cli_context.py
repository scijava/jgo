from unittest.mock import MagicMock

from jgo.cli.context import create_maven_context
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
