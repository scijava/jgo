import glob
import logging
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

import jgo

_logger = logging.getLogger(__name__)


IGNORE_JGORC = "--ignore-jgorc"
LINK_TYPE = "--link-type"
PARSINGTON_VERSION = "1.0.4"
PARSINGTON_ENDPOINT = "org.scijava:parsington:{}".format(PARSINGTON_VERSION)


def run_parsington(cache_dir, link_type, parsington_args):
    parser = jgo.jgo.jgo_parser()
    argv = (IGNORE_JGORC, LINK_TYPE, link_type, PARSINGTON_ENDPOINT) + parsington_args
    os.environ[jgo.jgo.jgo_cache_dir_environment_variable()] = cache_dir
    try:
        rv = jgo.jgo.run(parser=parser, argv=argv, stdout=subprocess.PIPE)
    finally:
        del os.environ[jgo.jgo.jgo_cache_dir_environment_variable()]
    return rv


def resolve_parsington(cache_dir, link_type, m2_repo):
    return jgo.resolve_dependencies(
        PARSINGTON_ENDPOINT, m2_repo=m2_repo, cache_dir=cache_dir, link_type=link_type
    )


class ParsingtonTest(unittest.TestCase):
    def test_resolve_hard(self):
        tmp_dir = tempfile.mkdtemp(prefix="jgo-test-cache-dir")
        m2_repo = os.path.join(str(pathlib.Path.home()), ".m2", "repository")
        try:
            _, workspace = resolve_parsington(
                cache_dir=tmp_dir, link_type="hard", m2_repo=m2_repo
            )
            jars = glob.glob(os.path.join(workspace, "*jar"))
            self.assertEqual(len(jars), 1, "Expected exactly one jar in workspace")
            self.assertEqual(
                jars[0],
                os.path.join(workspace, "parsington-%s.jar" % PARSINGTON_VERSION),
                "Expected parsington jar",
            )
            self.assertFalse(
                os.path.islink(jars[0]), "Expected hard link but found symbolic link."
            )
            self.assertTrue(os.path.isfile(jars[0]))
            self.assertGreaterEqual(
                os.stat(jars[0]).st_nlink,
                2,
                "Expected ref count of at least 2 for hard link.",
            )
        except OSError as e:
            if e.errno == 18:
                _logger.warning(
                    "Unable to cross-device hard link, skipping hard link test: %s",
                    str(e),
                )
            else:
                raise e
        finally:
            shutil.rmtree(tmp_dir)

    def test_resolve_soft(self):
        tmp_dir = tempfile.mkdtemp(prefix="jgo-test-cache-dir")
        m2_repo = os.path.join(str(pathlib.Path.home()), ".m2", "repository")
        try:
            _, workspace = resolve_parsington(
                cache_dir=tmp_dir, link_type="soft", m2_repo=m2_repo
            )
            jars = glob.glob(os.path.join(workspace, "*jar"))
            self.assertEqual(len(jars), 1, "Expected exactly one jar in workspace")
            self.assertEqual(
                jars[0],
                os.path.join(workspace, "parsington-%s.jar" % PARSINGTON_VERSION),
                "Expected parsington jar",
            )
            self.assertTrue(os.path.islink(jars[0]), "Expected soft link.")
        finally:
            shutil.rmtree(tmp_dir)

    def test_resolve_copy(self):
        tmp_dir = tempfile.mkdtemp(prefix="jgo-test-cache-dir")
        m2_repo = os.path.join(str(pathlib.Path.home()), ".m2", "repository")
        try:
            _, workspace = resolve_parsington(
                cache_dir=tmp_dir, link_type="copy", m2_repo=m2_repo
            )
            jars = glob.glob(os.path.join(workspace, "*jar"))
            self.assertEqual(len(jars), 1, "Expected exactly one jar in workspace")
            self.assertEqual(
                jars[0],
                os.path.join(workspace, "parsington-%s.jar" % PARSINGTON_VERSION),
                "Expected parsington jar",
            )
            self.assertFalse(
                os.path.islink(jars[0]), "Expected copied file but found symbolic link."
            )
            self.assertTrue(os.path.isfile(jars[0]))
            self.assertEqual(
                os.stat(jars[0]).st_nlink,
                1,
                "Expected ref count of exactly 1 for copied file.",
            )
        finally:
            shutil.rmtree(tmp_dir)

    def test_resolve_auto(self):
        tmp_dir = tempfile.mkdtemp(prefix="jgo-test-cache-dir")
        m2_repo = os.path.join(str(pathlib.Path.home()), ".m2", "repository")
        try:
            _, workspace = resolve_parsington(
                cache_dir=tmp_dir, link_type="auto", m2_repo=m2_repo
            )
            jars = glob.glob(os.path.join(workspace, "*jar"))
            self.assertEqual(len(jars), 1, "Expected exactly one jar in workspace")
            self.assertEqual(
                jars[0],
                os.path.join(workspace, "parsington-%s.jar" % PARSINGTON_VERSION),
                "Expected parsington jar",
            )
        finally:
            shutil.rmtree(tmp_dir)

    def test_run_jgo(self):
        tmp_dir = tempfile.mkdtemp(prefix="jgo-test-cache-dir")

        try:
            completed_process = run_parsington(
                cache_dir=tmp_dir, link_type="auto", parsington_args=("1+3",)
            )
            self.assertIsNotNone(completed_process)
            self.assertEqual(
                completed_process.returncode, 0, "Expected return code zero."
            )
            self.assertEqual(
                completed_process.stdout.decode("ascii").strip(), str(1 + 3)
            )
        finally:
            shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    unittest.main()
