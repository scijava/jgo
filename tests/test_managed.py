import glob
import logging
import os
import pathlib
import shutil
import tempfile
import unittest

import jgo
from jgo.jgo import InvalidEndpoint

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


def find_jar_matching(jars, pattern):
    for jar in jars:
        lastindex = jar.rindex(os.sep)
        if jar[lastindex:].find(pattern) != -1:
            return jar
    return None


class ManagedDependencyTest(unittest.TestCase):
    def test_resolve_managed(self):
        tmp_dir = tempfile.mkdtemp(prefix="jgo-test-cache-dir")
        m2_repo = os.path.join(str(pathlib.Path.home()), ".m2", "repository")
        try:
            _, workspace = resolve_managed(
                MANAGED_ENDPOINT, cache_dir=tmp_dir, m2_repo=m2_repo
            )
            jars = glob.glob(os.path.join(workspace, "*jar"))
            self.assertEqual(len(jars), 4, "Expected four jars in workspace")
            sj_common_jar = find_jar_matching(jars, "scijava-common")
            self.assertEqual(
                sj_common_jar,
                os.path.join(workspace, "scijava-common-%s.jar" % SJC_VERSION),
                "Expected scijava-common jar",
            )
            sj_optional_jar = find_jar_matching(jars, "scijava-optional")
            self.assertEqual(
                sj_optional_jar,
                os.path.join(
                    workspace, "scijava-optional-%s.jar" % SJC_OPTIONAL_VERSION
                ),
                "Expected scijava-optional jar",
            )

            pom = os.path.join(
                tmp_dir,
                "org.scijava",
                "scijava-common",
                SJC_VERSION,
                "d9deda31e3772a497c66ee3593296f33e918cda69b376c33039ba181dab14db4",
                "pom.xml",
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
            with self.assertRaises(InvalidEndpoint):
                resolve_managed(
                    MANAGED_PRIMARY_ENDPOINT, cache_dir=tmp_dir, m2_repo=m2_repo
                )
        finally:
            shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    unittest.main()
