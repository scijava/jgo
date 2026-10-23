"""
Maven artifact handlers: mapping a packaging type to its file extension.

A dependency's <type> (and a component's <packaging>) is not always the
extension of the file it names. Maven resolves each type to an
(extension, classifier) pair via an ArtifactHandler; this module mirrors
Maven's standard handlers.
"""

from __future__ import annotations

# type -> (extension, implied classifier)
ARTIFACT_HANDLERS: dict[str, tuple[str, str]] = {
    "jar": ("jar", ""),
    "pom": ("pom", ""),
    "war": ("war", ""),
    "ear": ("ear", ""),
    "rar": ("rar", ""),
    "maven-plugin": ("jar", ""),
    "bundle": ("jar", ""),
    "ejb": ("jar", ""),
    "ejb-client": ("jar", "client"),
    "test-jar": ("jar", "tests"),
    "java-source": ("jar", "sources"),
    "javadoc": ("jar", "javadoc"),
}


def artifact_handler(type: str) -> tuple[str, str]:
    """
    Get the file extension and implied classifier for a packaging type.

    Types without a standard handler (e.g. 'zip', 'aar') use the type itself
    as the extension, with no implied classifier.

    Args:
        type: The packaging type (e.g., 'jar', 'test-jar', 'maven-plugin').

    Returns:
        Tuple of (extension, implied_classifier), e.g. ('jar', 'tests').
    """
    return ARTIFACT_HANDLERS.get(type, (type, ""))
