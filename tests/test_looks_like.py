"""Tests for looks_like_* helper functions in coordinate parsing."""

from jgo.parse._coordinate import (
    looks_like_classifier,
    looks_like_main_class,
    looks_like_version,
)


class TestLooksLikeVersion:
    """Test version detection heuristic."""

    def test_standard_versions(self):
        """Standard versions start with a digit."""
        assert looks_like_version("1.0.0")
        assert looks_like_version("2.0.0-SNAPSHOT")
        assert looks_like_version("23.1.0-beta")
        assert looks_like_version("0.0.1")
        assert looks_like_version("10.2.3")

    def test_special_keywords(self):
        """Special Maven version keywords."""
        assert looks_like_version("LATEST")
        assert looks_like_version("RELEASE")
        assert looks_like_version("MANAGED")

    def test_special_keywords_case_insensitive(self):
        """Special keywords are case-insensitive."""
        assert looks_like_version("latest")
        assert looks_like_version("release")
        assert looks_like_version("managed")
        assert looks_like_version("LaTest")
        assert looks_like_version("ReLease")

    def test_not_versions(self):
        """Strings that don't look like versions."""
        assert not looks_like_version("MyClass")
        assert not looks_like_version("com.example.Main")
        assert not looks_like_version("v1.2.3")  # Starts with 'v', not digit
        assert not looks_like_version("alpha")
        assert not looks_like_version("beta")
        assert not looks_like_version("")

    def test_edge_cases(self):
        """Edge cases for version detection."""
        assert looks_like_version("1")  # Single digit
        assert looks_like_version("9999.9999.9999")  # Large numbers
        assert not looks_like_version("RC1")  # Starts with letter
        assert not looks_like_version("Beta2")  # Starts with letter


class TestLooksLikeClassifier:
    """Test Maven classifier detection heuristic."""

    def test_native_libraries(self):
        """Classifiers starting with 'natives-' for native libraries."""
        assert looks_like_classifier("natives-linux")
        assert looks_like_classifier("natives-windows")
        assert looks_like_classifier("natives-macos")
        assert looks_like_classifier("natives-linux-x86_64")
        assert looks_like_classifier("natives-windows-amd64")

    def test_native_libraries_case_insensitive(self):
        """Native library classifiers are case-insensitive."""
        assert looks_like_classifier("NATIVES-linux")
        assert looks_like_classifier("Natives-Windows")
        assert looks_like_classifier("NaTiVeS-macos")

    def test_standard_classifiers(self):
        """Standard Maven classifiers."""
        assert looks_like_classifier("sources")
        assert looks_like_classifier("javadoc")
        assert looks_like_classifier("tests")
        assert looks_like_classifier("shaded")
        assert looks_like_classifier("uber")

    def test_standard_classifiers_case_insensitive(self):
        """Standard classifiers are case-insensitive."""
        assert looks_like_classifier("SOURCES")
        assert looks_like_classifier("JavaDoc")
        assert looks_like_classifier("TESTS")
        assert looks_like_classifier("Shaded")
        assert looks_like_classifier("UBER")

    def test_architecture_patterns(self):
        """Classifiers containing architecture names."""
        assert looks_like_classifier("linux-x86_64")
        assert looks_like_classifier("windows-amd64")
        assert looks_like_classifier("macos-arm64")
        assert looks_like_classifier("linux-aarch64")
        assert looks_like_classifier("windows-i386")
        assert looks_like_classifier("linux-i686")
        assert looks_like_classifier("linux-armv7")
        assert looks_like_classifier("raspbian-armhf")

    def test_os_patterns(self):
        """Classifiers containing OS names (require hyphen prefix)."""
        assert looks_like_classifier("natives-linux")
        assert looks_like_classifier("natives-windows")
        assert looks_like_classifier("natives-macos")
        assert looks_like_classifier("lib-osx")
        assert looks_like_classifier("app-darwin")
        assert looks_like_classifier("lib-freebsd")
        assert looks_like_classifier("app-solaris")

    def test_combined_os_arch_patterns(self):
        """Classifiers with combined OS and architecture."""
        assert looks_like_classifier("linux-x86_64")
        assert looks_like_classifier("windows-amd64")
        assert looks_like_classifier("darwin-arm64")
        assert looks_like_classifier("freebsd-amd64")
        assert looks_like_classifier("solaris-i386")

    def test_case_insensitive_patterns(self):
        """All patterns are case-insensitive."""
        assert looks_like_classifier("LINUX-X86_64")
        assert looks_like_classifier("Windows-AMD64")
        assert looks_like_classifier("MacOS-ARM64")
        assert looks_like_classifier("natives-DARWIN")
        assert looks_like_classifier("lib-FreeBSD")

    def test_not_classifiers_version_like(self):
        """Version strings should not be detected as classifiers."""
        assert not looks_like_classifier("1.0.0")
        assert not looks_like_classifier("2.0.0-SNAPSHOT")
        assert not looks_like_classifier("3.1.0-beta")
        assert not looks_like_classifier("LATEST")
        assert not looks_like_classifier("RELEASE")

    def test_not_classifiers_class_like(self):
        """Class names should not be detected as classifiers."""
        assert not looks_like_classifier("Main")
        assert not looks_like_classifier("MyClass")
        assert not looks_like_classifier("com.example.Main")

    def test_not_classifiers_artifact_like(self):
        """Artifact IDs should not be detected as classifiers."""
        assert not looks_like_classifier("my-artifact")
        assert not looks_like_classifier("some-lib")
        assert not looks_like_classifier("foo-bar")
        assert not looks_like_classifier("jython-standalone")

    def test_not_classifiers_partial_matches(self):
        """Strings that partially match but shouldn't be classifiers."""
        assert not looks_like_classifier("source")  # Not exactly "sources"
        assert not looks_like_classifier("sourcesX")  # Extra characters
        assert not looks_like_classifier("test")  # Not exactly "tests"
        assert not looks_like_classifier("shade")  # Not exactly "shaded"

    def test_not_classifiers_artifact_id_components(self):
        """
        Tokens that appear in artifact IDs, not as classifiers.

        These are commonly found as parts of artifact names like:
        - netty-all, groovy-all (NOT artifactId-version-all.jar)
        - antlr-runtime, antlr4-runtime (NOT artifactId-version-runtime.jar)
        - jline-native (NOT artifactId-version-native.jar)
        """
        assert not looks_like_classifier("all")  # netty-all, groovy-all
        assert not looks_like_classifier("runtime")  # antlr-runtime, antlr4-runtime
        assert not looks_like_classifier(
            "native"
        )  # jline-native (singular, not natives-)
        assert not looks_like_classifier("classes")  # netty-tcnative-classes
        assert not looks_like_classifier("dependencies")  # resteasy-dependencies

    def test_not_classifiers_version_qualifiers(self):
        """
        Tokens that appear as version qualifiers, not classifiers.

        Examples from actual Maven repos:
        - guava-33.4.8-android (android is part of version, NOT classifier)
        - guava-33.4.8-jre (jre is part of version, NOT classifier)
        - htrace-4.1.0-incubating (incubating is part of version)

        Verified: maven.scijava.org finds NO examples of "android" as classifier,
        but DOES find "linux" as classifier (e.g., javafx-fxml-23.0.2-linux.jar).
        """
        assert not looks_like_classifier("jre")  # guava uses as version: 33.4.8-jre
        assert not looks_like_classifier("incubating")  # Apache: 4.1.0-incubating

    def test_not_classifiers_project_specific(self):
        """Project-specific strings that aren't general classifiers."""
        # Project/library names
        assert not looks_like_classifier("guava")
        assert not looks_like_classifier("fiji4")
        assert not looks_like_classifier("scijava")
        assert not looks_like_classifier("swing")

        # Git commit hashes
        assert not looks_like_classifier("c034a77")
        assert not looks_like_classifier("cb22e71335")

        # Version-like suffixes
        assert not looks_like_classifier("mk1")
        assert not looks_like_classifier("release3")

        # Too specific/niche
        assert not looks_like_classifier("no_aop")
        assert not looks_like_classifier("noaop")
        assert not looks_like_classifier("inv")

    def test_not_classifiers_empty_string(self):
        """Empty string is not a classifier."""
        assert not looks_like_classifier("")

    def test_edge_cases_with_natives(self):
        """Edge cases for natives- prefix."""
        assert looks_like_classifier("natives-")  # Just the prefix
        assert looks_like_classifier("natives-custom")  # With custom suffix

    def test_additional_architectures(self):
        """Additional architecture patterns found in the wild."""
        # x86 32-bit variants
        assert looks_like_classifier("lib-i586")
        assert looks_like_classifier("app-i486")

        # ARM variants
        assert looks_like_classifier("lib-arm")
        assert looks_like_classifier("lib-armv6")
        assert looks_like_classifier("raspbian-armv6hf")
        assert looks_like_classifier("lib-aarch_64")  # Underscore variant

        # PowerPC
        assert looks_like_classifier("lib-ppc")
        assert looks_like_classifier("lib-ppc64")
        assert looks_like_classifier("lib-ppc64le")
        assert looks_like_classifier("lib-powerpc")

        # Itanium
        assert looks_like_classifier("lib-ia64")

    def test_additional_os_platforms(self):
        """Additional OS platforms found in the wild."""
        # These work as standalone classifiers (confirmed in JavaFX)
        assert looks_like_classifier("mac")
        assert looks_like_classifier("win")

        # These only work with prefixes (natives-, or -arch)
        assert looks_like_classifier("natives-android")  # gluegen-rt
        assert looks_like_classifier("osx-x86_64")  # netty
        assert looks_like_classifier("natives-solaris")  # gluegen-rt

        # Standalone forms that don't exist (only in compounds)
        assert not looks_like_classifier(
            "android"
        )  # Only in Guava as version: 33.4.8-android
        assert not looks_like_classifier("osx")  # Only in compounds: osx-x86_64
        assert not looks_like_classifier(
            "solaris"
        )  # Only with natives-: natives-solaris-amd64
        assert not looks_like_classifier("darwin")  # Not found in Maven Central
        assert not looks_like_classifier("freebsd")  # Not found in Maven Central

    def test_standalone_platform_classifiers(self):
        """Standalone classifiers for platforms."""
        # Universal/cross-platform
        assert looks_like_classifier("universal")

        # Note: 'all', 'runtime', 'native', 'classes', 'dependencies' are typically
        # artifact ID components (e.g., netty-all, antlr-runtime, jline-native)
        # not classifiers, so they are intentionally NOT matched

    def test_underscore_separators(self):
        """Classifiers using underscores instead of hyphens."""
        assert looks_like_classifier("linux_64")
        assert looks_like_classifier("linux_32")
        assert looks_like_classifier("natives_linux")
        assert looks_like_classifier("lib_aarch_64")
        assert looks_like_classifier("app_x86_64")

    def test_real_world_examples(self):
        """Real-world classifier examples from Maven Central."""
        # LWJGL native library classifiers
        assert looks_like_classifier("natives-linux")
        assert looks_like_classifier("natives-windows")
        assert looks_like_classifier("natives-macos")

        # Platform-specific classifiers
        assert looks_like_classifier("linux-x86_64")
        assert looks_like_classifier("osx-aarch64")
        assert looks_like_classifier("windows-x86_64")

        # Standard Maven classifiers
        assert looks_like_classifier("sources")
        assert looks_like_classifier("javadoc")
        assert looks_like_classifier("tests")

        # From actual .m2/repository analysis - confirmed classifiers
        assert looks_like_classifier("aarch_64")  # Arch (gluegen-rt)
        assert looks_like_classifier("aarch64")  # Arch (gluegen-rt)
        assert looks_like_classifier(
            "amd64"
        )  # Arch (gluegen-rt-2.6.0-natives-linux-amd64.jar)
        assert looks_like_classifier(
            "arm64"
        )  # Arch (openblas-0.3.26-1.5.10-macosx-arm64.jar)
        assert looks_like_classifier("armv6")  # Arch
        assert looks_like_classifier("armv6hf")  # Arch
        assert looks_like_classifier(
            "i586"
        )  # Arch (gluegen-rt-2.3.2-natives-linux-i586.jar)
        assert looks_like_classifier(
            "javadoc"
        )  # Standard (scijava-common-2.89.0-javadoc.jar)
        assert looks_like_classifier(
            "linux"
        )  # OS standalone (javafx-fxml-23.0.2-linux.jar)
        assert looks_like_classifier("linux_64")  # OS+arch combo
        assert looks_like_classifier(
            "mac"
        )  # OS standalone (javafx-fxml-23.0.2-mac.jar)
        assert looks_like_classifier(
            "macos"
        )  # OS (lwjgl-openvr-3.3.3-natives-macos.jar)
        assert looks_like_classifier("shaded")  # Build type
        assert looks_like_classifier("sources")  # Standard (scifio-0.46.0-sources.jar)
        assert looks_like_classifier(
            "tests"
        )  # Standard (scifio-labeling-0.3.2-SNAPSHOT-tests.jar)
        assert looks_like_classifier("uber")  # Build type
        assert looks_like_classifier("universal")  # Cross-platform
        assert looks_like_classifier(
            "win"
        )  # OS standalone (javafx-fxml-23.0.2-win.jar)
        assert looks_like_classifier(
            "windows"
        )  # OS (lwjgl-openvr-3.3.3-natives-windows.jar)
        assert looks_like_classifier(
            "x86_64"
        )  # Arch (netty-epoll-4.1.75.Final-linux-x86_64.jar)


class TestLooksLikeMainClass:
    """Test Java main class name validation."""

    def test_simple_class_names(self):
        """Valid simple (unqualified) class names."""
        assert looks_like_main_class("MyClass")
        assert looks_like_main_class("Main")
        assert looks_like_main_class("Test")
        assert looks_like_main_class("A")  # Single letter

    def test_qualified_class_names(self):
        """Valid package-qualified class names."""
        assert looks_like_main_class("com.example.Main")
        assert looks_like_main_class("org.scijava.script.ScriptREPL")
        assert looks_like_main_class("sc.fiji.Main")
        assert looks_like_main_class("a.b.C")  # Minimal qualified name

    def test_class_names_with_digits(self):
        """Class names can contain digits (after first character)."""
        assert looks_like_main_class("MyClass2")
        assert looks_like_main_class("Test123")
        assert looks_like_main_class("V8Engine")
        assert looks_like_main_class("com.example.Class2")

    def test_class_names_with_special_chars(self):
        """Class names can contain $ and _ per Java spec."""
        assert looks_like_main_class("_MyClass")
        assert looks_like_main_class("$Special")
        assert looks_like_main_class("My_Class")
        assert looks_like_main_class("My$Inner")
        assert looks_like_main_class("com.example._Private")
        assert looks_like_main_class("org.example.$Generated")

    def test_invalid_starts_with_digit(self):
        """Class names cannot start with a digit."""
        assert not looks_like_main_class("2Class")
        assert not looks_like_main_class("9Main")
        assert not looks_like_main_class("123Test")

    def test_invalid_contains_hyphen(self):
        """Class names cannot contain hyphens."""
        assert not looks_like_main_class("my-class")
        assert not looks_like_main_class("com.my-example.Main")
        assert not looks_like_main_class("MyClass-v2")

    def test_invalid_empty_tokens(self):
        """Class names cannot have empty tokens (consecutive dots)."""
        assert not looks_like_main_class("com..Main")
        assert not looks_like_main_class(".Main")
        assert not looks_like_main_class("Main.")
        assert not looks_like_main_class("com...example.Main")

    def test_invalid_empty_string(self):
        """Empty string is not a valid class name."""
        assert not looks_like_main_class("")

    def test_version_strings_not_classes(self):
        """Version strings should be rejected (violate identifier rules)."""
        assert not looks_like_main_class("2.0.0")  # Starts with digit
        assert not looks_like_main_class("1.0-SNAPSHOT")  # Contains hyphen
        assert not looks_like_main_class("23.1.0-beta")  # Contains hyphen
        assert not looks_like_main_class("v1.2.3")  # Second token starts with digit

    def test_special_version_keywords_are_valid_identifiers(self):
        """
        Special keywords are technically valid Java identifiers.

        Note: The parsing logic handles these as special cases,
        but grammatically they follow Java identifier rules.
        """
        assert looks_like_main_class("LATEST")
        assert looks_like_main_class("RELEASE")
        assert looks_like_main_class("MANAGED")

    def test_common_artifact_ids_not_classes(self):
        """Common artifact naming patterns that aren't valid classes."""
        assert not looks_like_main_class("my-artifact")
        assert not looks_like_main_class("some-lib")
        assert not looks_like_main_class("foo-bar-baz")

    def test_maven_coordinate_parts_not_classes(self):
        """Parts of Maven coordinates that look version-like."""
        assert not looks_like_main_class("2.0.0")
        assert not looks_like_main_class("1.0-alpha")
        assert not looks_like_main_class("3.1.0-beta.1")
        assert not looks_like_main_class("1.0-20231201.123456-1")  # Timestamp snapshot
