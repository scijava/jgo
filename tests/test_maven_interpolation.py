"""
Test property interpolation in Maven POMs.

This test validates that property interpolation works correctly across:
- Parent POM inheritance
- Dependency management
- Both SimpleResolver (pure Python) and MavenResolver (mvn-based)

Ported from db-xml-maven/tests/test_maven.py
"""

from re import match

import pytest

from jgo.maven import MavenContext, MavenResolver


class TestPropertyInterpolation:
    """Test that ${...} property expressions are correctly interpolated."""

    @pytest.mark.xfail(reason="TODO: Fix G/A/C property interpolation in model.py:1022-1032")
    def test_interpolate_syscall(self):
        """
        Test property interpolation with both SimpleResolver and MavenResolver.

        Uses pom-scijava 35.1.1 as a complex real-world test case with:
        - Deep parent POM inheritance
        - Extensive dependency management
        - Property-based versioning
        """
        # Test with SimpleResolver (pure Python)
        maven = MavenContext()
        pom_simple = maven.project("org.scijava", "pom-scijava").at_version("35.1.1").pom()
        self.assert_pom_interpolated(pom_simple)

        # Test with MavenResolver (mvn-based)
        maven_syscall = MavenContext(resolver=MavenResolver("mvn"))
        maven_syscall.resolver.mvn_flags = ["-o"] + maven_syscall.resolver.mvn_flags
        pom_syscall = maven_syscall.project("org.scijava", "pom-scijava").at_version("35.1.1").pom()
        self.assert_pom_interpolated(pom_syscall)

        # Ensure both resolvers produce identical results
        self.assert_equal_xml(pom_syscall, pom_simple)

    def assert_pom_interpolated(self, pom):
        """
        Validate that all managed dependency versions are fully interpolated.

        Good: "1.16.0"
        Bad: "${batik.version}"
        """
        assert pom is not None
        for dep in pom.dependencies(managed=True):
            # Ensure all versions are populated with actual version numbers,
            # not unresolved property references like ${foo.version}
            assert dep.version is not None, f"Dependency {dep} has no version"
            assert match(r"\d+($|\.\d+)", dep.version), \
                f"Dependency {dep} has uninterpolated version: {dep.version}"

    def assert_equal_xml(self, xml1, xml2):
        """
        Compare two POM XML objects for equality.

        Ignores non-deterministic elements like timestamps.
        """
        lines1 = self.lockdown(xml1).dump().splitlines()
        lines2 = self.lockdown(xml2).dump().splitlines()
        assert len(lines1) > 100, "POM seems too small, might be invalid"
        assert lines1 == lines2, "POMs differ between SimpleResolver and MavenResolver"

    def lockdown(self, xml):
        """
        Normalize non-deterministic values in XML for comparison.

        Replaces timestamp values with a constant to allow comparison.
        """
        # Ignore elements with non-deterministic values such as datestamps.
        ignored_elements = (
            "build/pluginManagement/plugins/plugin/configuration/archive/manifestEntries/Implementation-Date",
            "build/pluginManagement/plugins/plugin/executions/execution/configuration/archive/manifestEntries/Implementation-Date",
        )
        for p in ignored_elements:
            for el in xml.elements(p):
                el.text = "IGNORED"
        return xml


class TestPropertyInterpolationEdgeCases:
    """Test edge cases in property interpolation."""

    def test_project_properties(self):
        """Test that special ${project.*} properties are interpolated."""
        maven = MavenContext()
        # Use a simple POM that we know uses project properties
        pom = maven.project("org.scijava", "pom-scijava").at_version("35.1.1").pom()

        # Verify basic POM properties are accessible
        assert pom.groupId is not None
        assert pom.artifactId == "pom-scijava"
        assert pom.version == "35.1.1"

    @pytest.mark.xfail(reason="TODO: Fix G/A/C property interpolation in model.py:1022-1032")
    def test_version_properties_in_dependency_management(self):
        """
        Test that version properties in <dependencyManagement> are interpolated.

        This is critical for BOMs (Bill of Materials) which use property-based
        versioning extensively.
        """
        maven = MavenContext()
        pom = maven.project("org.scijava", "pom-scijava").at_version("35.1.1").pom()

        managed_deps = pom.dependencies(managed=True)
        assert len(managed_deps) > 0, "No managed dependencies found"

        # All managed dependency versions should be fully resolved
        for dep in managed_deps:
            if dep.version:  # Some may be None if managed by parent
                assert "${" not in dep.version, \
                    f"Uninterpolated property in {dep.groupId}:{dep.artifactId}: {dep.version}"
