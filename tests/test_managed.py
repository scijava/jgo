import glob
from jgo.jgo import InvalidEndpoint
import jgo
import os
import pathlib
import unittest
import shutil
import tempfile

import logging

_logger = logging.getLogger(__name__)
_logger.level = logging.INFO

SJC_VERSION = "2.87.0"
SJC_OPTIONAL_VERSION = "1.0.0"
MANAGED_ENDPOINT = (
    "org.scijava:scijava-common:{}+org.scijava:scijava-optional:MANAGED".format(
        SJC_VERSION
    )
)
MANAGED_PRIMARY_ENDPOINT = "org.scijava:scijava-common:MANAGED"
REPOSITORIES = {"scijava.public": "https://maven.scijava.org/content/groups/public"}


def resolve_managed(endpoint, cache_dir, m2_repo):
    return jgo.resolve_dependencies(
        endpoint,
        m2_repo=m2_repo,
        cache_dir=cache_dir,
        manage_dependencies=True,
        repositories=REPOSITORIES,
    )


class ManagedDependencyTest(unittest.TestCase):
    def test_resolve_managed(self):
        tmp_dir = tempfile.mkdtemp(prefix="jgo-test-cache-dir")
        m2_repo = os.path.join(str(pathlib.Path.home()), ".m2", "repository")
        try:
            _, workspace = resolve_managed(
                MANAGED_ENDPOINT, cache_dir=tmp_dir, m2_repo=m2_repo
            )
            jars = glob.glob(os.path.join(workspace, "*jar"))
            self.assertEqual(len(jars), 4, "Expected two jars in workspace")
            self.assertEqual(
                jars[2],
                os.path.join(workspace, "scijava-common-%s.jar" % SJC_VERSION),
                "Expected scijava-common jar",
            )
            self.assertEqual(
                jars[3],
                os.path.join(
                    workspace, "scijava-optional-%s.jar" % SJC_OPTIONAL_VERSION
                ),
                "Expected scijava-optional jar",
            )
            pom = (
                    os.path.join(tmp_dir, 'org.scijava', 'scijava-common', 'cdcf7e6e4f89d0815be7f9c57eae1fa3361f9b75f0eaa89d4099a731690d0c5e', 'pom.xml')
            )
            with open(pom) as f:
                if "RELEASE" in f.read():
                    self.fail(
                        "Expected no RELEASE version string in managed dependency"
                    )
        finally:
            shutil.rmtree(tmp_dir)

    def test_managed_primary(self):
        tmp_dir = tempfile.mkdtemp(prefix="jgo-test-cache-dir")
        m2_repo = os.path.join(str(pathlib.Path.home()), ".m2", "repository")
        try:
            with self.assertRaises(InvalidEndpoint) as context:
                resolve_managed(
                    MANAGED_PRIMARY_ENDPOINT, cache_dir=tmp_dir, m2_repo=m2_repo
                )
        finally:
            shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    unittest.main()
