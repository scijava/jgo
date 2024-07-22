from re import match
from unittest import TestCase

from jgo import maven


class MavenTest(TestCase):
    def test_interpolate_syscall(self):
        # Interpolate with SimpleResolver.
        env = maven.Environment()
        pom = env.project("org.scijava", "pom-scijava").at_version("35.1.1").pom()
        self.assert_pom(pom)

        # Interpolate with SysCallResolver.
        env.resolver = maven.SysCallResolver("mvn")
        env.resolver.mvn_flags = ["-o"] + env.resolver.mvn_flags
        pom_syscall = env.project("org.scijava", "pom-scijava").at_version("35.1.1").pom()
        self.assert_pom(pom_syscall)

        # Ensure they match.
        pom = env.project("org.scijava", "pom-scijava").at_version("35.1.1").pom()
        self.assert_equal_xml(pom_syscall, pom)

    def assert_pom(self, pom):
        assert pom is not None
        for dep in pom.dependencies(managed=True):
            # Ensure all versions are populated.
            # Good: 1.16 / Bad: ${batik.version}
            assert match("\\d+($|\\.\\d+)", dep.version), dep

    def assert_equal_xml(self, xml1, xml2):
        lines1 = self.lockdown(xml1).dump().splitlines()
        lines2 = self.lockdown(xml2).dump().splitlines()
        assert len(lines1) > 100
        self.assertListEqual(lines1, lines2)

    def lockdown(self, xml):
        # Ignore elements with non-determinstic values such as datestamps.
        ignored_elements = (
            "build/pluginManagement/plugins/plugin/configuration/archive/manifestEntries/Implementation-Date",
            "build/pluginManagement/plugins/plugin/executions/execution/configuration/archive/manifestEntries/Implementation-Date",
        )
        for p in ignored_elements:
            for el in xml.elements(p):
                print(f"IGNORING {el}")
                el.text = "IGNORED"
        return xml
