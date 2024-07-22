import os
import pathlib
import subprocess
import sys
import unittest
from typing import Dict, Tuple
from unittest.mock import MagicMock, patch

from jgo.jgo import (
    Endpoint,
    ExecutableNotFound,
    HelpRequested,
    InvalidEndpoint,
    NoEndpointProvided,
    NoMainClassInManifest,
    _jgo_main,
    executable_path_or_raise,
    jgo_parser,
    run,
)
from jgo.util import main_from_endpoint


def _call_args(mock: MagicMock) -> Tuple[Tuple, Dict]:
    """
    Returns the arguments and keyword arguments passed in a mock call.
    :param mock: The mock that was called
    :return: A tuple, where the first element is the args passed in the call,
        and the second element is the keyword args passed in the call
    """
    if sys.version_info.minor >= 8:
        return (mock.call_args.args, mock.call_args.kwargs)
    return (mock.call_args[0], mock.call_args[1])


class TestExceptions(unittest.TestCase):
    def test_find_tool(self):
        with self.assertRaises(ExecutableNotFound):
            executable_path_or_raise("does not exist")

    def test_help_without_endpoint(self):
        parser = jgo_parser()
        argv = ["--help"]

        with self.assertRaises(HelpRequested):
            run(parser, argv)

    def test_no_endpoint(self):
        parser = jgo_parser()
        argv = []

        with self.assertRaises(NoEndpointProvided):
            run(parser, argv)

    def _test_help_before_endpoint(self):
        # Does not work yet
        parser = jgo_parser()
        argv = ["--help", "org.codehaus.groovy:groovy-groovysh"]

        with self.assertRaises(HelpRequested):
            run(parser, argv)

    def _test_help_after_endpoint(self):
        # Does not work yet
        parser = jgo_parser()
        argv = ["org.codehaus.groovy:groovy-groovysh", "--help"]

        with self.assertRaises(HelpRequested):
            run(parser, argv)

    def test_too_many_colons(self):
        parser = jgo_parser()
        argv = ["invalid:endpoint:syntax:too:many:colons"]

        with self.assertRaises(NoEndpointProvided):
            run(parser, argv)

    def test_extra_endpoint_elements(self):
        parser = jgo_parser()
        argv = [
            (
                "io.netty:netty-transport-native-epoll:4.1.79.Final:"
                "linux-x86_64:FakeMainClass:SomethingElse"
            )
        ]

        with self.assertRaises(NoEndpointProvided):
            run(parser, argv)

    def test_additional_endpoint_too_many_colons(self):
        parser = jgo_parser()
        argv = [
            "--additional-endpoints",
            "invalid:endpoint:syntax:too:many:colons",
            "mvxcvi:cljstyle",
        ]

        with self.assertRaisesRegex(InvalidEndpoint, "Too many elements"):
            run(parser, argv)

    def test_too_few_colons(self):
        parser = jgo_parser()
        argv = ["invalid:"]

        with self.assertRaises(subprocess.CalledProcessError):
            run(parser, argv)

    def test_additional_endpoint_too_few_colons(self):
        parser = jgo_parser()
        argv = ["--additional-endpoints", "invalid", "mvxcvi:cljstyle"]

        with self.assertRaisesRegex(InvalidEndpoint, "Not enough artifacts specified"):
            run(parser, argv)

    def test_invalid_primary_endpoint_managed(self):
        parser = jgo_parser()
        argv = [
            "--manage-dependencies",
            "org.scijava:scijava-optional:MANAGED+org.scijava:scijava-common:MANAGED",
        ]

        with self.assertRaisesRegex(InvalidEndpoint, "version=MANAGED"):
            run(parser, argv)

    def test_unresolvable_endpoint(self):
        parser = jgo_parser()
        argv = ["unresolvable:endpoint"]

        with self.assertRaises(subprocess.CalledProcessError):
            run(parser, argv)

    def test_no_main_class_in_manifest(self):
        parser = jgo_parser()
        argv = ["org.codehaus.groovy:groovy-groovysh"]

        with self.assertRaises(NoMainClassInManifest):
            run(parser, argv)


class TestMainCaughtExceptions(unittest.TestCase):
    def test_help_without_endpoint(self):
        argv = ["--help"]

        rv = _jgo_main(argv)
        self.assertEqual(rv, 0, "Expected return code zero.")

    def test_without_endpoint(self):
        argv = []

        rv = _jgo_main(argv)
        self.assertEqual(rv, 254, "Expected return code 254.")

    def test_too_few_colons(self):
        argv = ["invalid:"]

        rv = _jgo_main(argv)
        self.assertEqual(rv, 1, "Expected return code one.")


class TestRun(unittest.TestCase):
    @patch("jgo.jgo._run")
    def test_basic(self, run_mock):
        parser = jgo_parser()
        argv = ["com.pinterest:ktlint", "-F", "/c/path/to/file.kt"]

        run(parser, argv)
        self.assertTrue(run_mock.called)
        args, _ = _call_args(run_mock)
        workspace = args[0]
        primary_endpoint: Endpoint = args[1]
        jvm_args = args[2]
        program_args = args[3]
        additional_jars = args[4]
        stdout = args[5]
        stderr = args[6]
        self.assertIsInstance(workspace, str)
        self.assertIsInstance(primary_endpoint, Endpoint)
        self.assertEqual(primary_endpoint.groupId, "com.pinterest")
        self.assertEqual(primary_endpoint.artifactId, "ktlint")
        self.assertEqual(jvm_args, [])
        self.assertEqual(program_args, ["-F", "/c/path/to/file.kt"])
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)

    @patch("jgo.jgo._run")
    def test_jvm_args(self, run_mock):
        parser = jgo_parser()
        argv = [
            "-Xms1G",
            "--add-opens",
            "java.base/java.lang=ALL-UNNAMED",
            "com.pinterest:ktlint",
            "-F",
            "/c/path/to/file.kt",
        ]

        run(parser, argv)
        self.assertTrue(run_mock.called)
        args, _ = _call_args(run_mock)
        workspace = args[0]
        primary_endpoint: Endpoint = args[1]
        jvm_args = args[2]
        program_args = args[3]
        additional_jars = args[4]
        stdout = args[5]
        stderr = args[6]
        self.assertIsInstance(workspace, str)
        self.assertIsInstance(primary_endpoint, Endpoint)
        self.assertEqual(primary_endpoint.groupId, "com.pinterest")
        self.assertEqual(primary_endpoint.artifactId, "ktlint")
        self.assertEqual(
            jvm_args, ["-Xms1G", "--add-opens", "java.base/java.lang=ALL-UNNAMED"]
        )
        self.assertEqual(program_args, ["-F", "/c/path/to/file.kt"])
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)

    @patch("jgo.jgo._run")
    def test_double_hyphen(self, run_mock):
        parser = jgo_parser()
        argv = [
            "--add-opens",
            "java.base/java.lang=ALL-UNNAMED",
            "com.pinterest:ktlint",
            "--",
            "-F",
            "/c/path/to/file.kt",
        ]

        run(parser, argv)
        self.assertTrue(run_mock.called)
        args, _ = _call_args(run_mock)
        workspace = args[0]
        primary_endpoint: Endpoint = args[1]
        jvm_args = args[2]
        program_args = args[3]
        additional_jars = args[4]
        stdout = args[5]
        stderr = args[6]
        self.assertIsInstance(workspace, str)
        self.assertIsInstance(primary_endpoint, Endpoint)
        self.assertEqual(primary_endpoint.groupId, "com.pinterest")
        self.assertEqual(primary_endpoint.artifactId, "ktlint")
        self.assertEqual(jvm_args, ["--add-opens", "java.base/java.lang=ALL-UNNAMED"])
        self.assertEqual(program_args, ["--", "-F", "/c/path/to/file.kt"])
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)

    @patch("jgo.jgo._run")
    def test_additional_endpoints(self, run_mock):
        parser = jgo_parser()
        argv = [
            "-q",
            "--additional-endpoints",
            "io.netty:netty-transport-native-epoll",
            "org.clojure:clojure",
            "org.scijava:parsington",
            "-F",
            "/c/path/to/file.kt",
        ]

        run(parser, argv)
        self.assertTrue(run_mock.called)
        args, _ = _call_args(run_mock)
        workspace = args[0]
        primary_endpoint: Endpoint = args[1]
        jvm_args = args[2]
        program_args = args[3]
        additional_jars = args[4]
        stdout = args[5]
        stderr = args[6]
        self.assertIsInstance(workspace, str)
        self.assertIsInstance(primary_endpoint, Endpoint)
        self.assertEqual(primary_endpoint.groupId, "org.scijava")
        self.assertEqual(primary_endpoint.artifactId, "parsington")
        self.assertEqual(jvm_args, [])
        self.assertEqual(program_args, ["-F", "/c/path/to/file.kt"])
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)

        with open("{}/{}".format(workspace, "coordinates.txt")) as fh:
            coordinates = fh.read()

        self.assertIn("io.netty:netty-transport-native-epoll", coordinates)
        self.assertIn("org.clojure:clojure", coordinates)

    @patch("jgo.jgo._run")
    def test_additional_endpoints_with_jvm_args(self, run_mock):
        parser = jgo_parser()
        argv = [
            "-q",
            "--additional-endpoints",
            "io.netty:netty-transport-native-epoll",
            "org.clojure:clojure",
            "--add-opens",
            "java.base/java.lang=ALL-UNNAMED",
            "org.scijava:parsington",
            "-F",
            "/c/path/to/file.kt",
        ]

        run(parser, argv)
        self.assertTrue(run_mock.called)
        args, _ = _call_args(run_mock)
        workspace = args[0]
        primary_endpoint: Endpoint = args[1]
        jvm_args = args[2]
        program_args = args[3]
        additional_jars = args[4]
        stdout = args[5]
        stderr = args[6]
        self.assertIsInstance(workspace, str)
        self.assertIsInstance(primary_endpoint, Endpoint)
        self.assertEqual(primary_endpoint.groupId, "org.scijava")
        self.assertEqual(primary_endpoint.artifactId, "parsington")
        self.assertEqual(jvm_args, ["--add-opens", "java.base/java.lang=ALL-UNNAMED"])
        self.assertEqual(program_args, ["-F", "/c/path/to/file.kt"])
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)

        with open("{}/{}".format(workspace, "coordinates.txt")) as fh:
            coordinates = fh.read()

        self.assertIn("io.netty:netty-transport-native-epoll", coordinates)
        self.assertIn("org.clojure:clojure", coordinates)

    @patch("jgo.jgo.default_config")
    @patch("jgo.jgo._run")
    def test_shortcut(self, run_mock, config_mock):
        parser = jgo_parser()
        argv = ["--ignore-jgorc", "ktlint"]

        config_mock.return_value = {
            "settings": {"cacheDir": os.path.join(str(pathlib.Path.home()), ".jgo")},
            "repositories": {},
            "shortcuts": {"ktlint": "com.pinterest:ktlint"},
        }

        run(parser, argv)
        self.assertTrue(config_mock.called)
        self.assertTrue(run_mock.called)
        args, _ = _call_args(run_mock)
        workspace = args[0]
        primary_endpoint: Endpoint = args[1]
        jvm_args = args[2]
        program_args = args[3]
        additional_jars = args[4]
        stdout = args[5]
        stderr = args[6]
        self.assertIsInstance(workspace, str)
        self.assertIsInstance(primary_endpoint, Endpoint)
        self.assertEqual(primary_endpoint.groupId, "com.pinterest")
        self.assertEqual(primary_endpoint.artifactId, "ktlint")
        self.assertEqual(jvm_args, [])
        self.assertEqual(program_args, [])
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)

    @patch("jgo.jgo._run")
    def test_classifier(self, run_mock):
        parser = jgo_parser()
        argv = [
            (
                "io.netty:netty-transport-native-epoll:4.1.79.Final:"
                "linux-x86_64:FakeMainClass"
            )
        ]

        run(parser, argv)
        self.assertTrue(run_mock.called)
        args, _ = _call_args(run_mock)
        workspace = args[0]
        primary_endpoint: Endpoint = args[1]
        jvm_args = args[2]
        program_args = args[3]
        additional_jars = args[4]
        stdout = args[5]
        stderr = args[6]
        self.assertIsInstance(workspace, str)
        self.assertIsInstance(primary_endpoint, Endpoint)
        self.assertEqual(primary_endpoint.groupId, "io.netty")
        self.assertEqual(primary_endpoint.artifactId, "netty-transport-native-epoll")
        self.assertEqual(primary_endpoint.classifier, "linux-x86_64")
        self.assertEqual(jvm_args, [])
        self.assertEqual(program_args, [])
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)

    @patch("jgo.jgo._run")
    def test_program_arg_path_windows_drive(self, run_mock):
        parser = jgo_parser()
        argv = [
            "-r",
            "clojars=https://clojars.org/repo/",
            "mvxcvi:cljstyle",
            "fix",
            "c:/path/to/file.clj",
        ]

        run(parser, argv)
        self.assertTrue(run_mock.called)
        workspace = run_mock.call_args.args[0]
        primary_endpoint: Endpoint = run_mock.call_args.args[1]
        jvm_args = run_mock.call_args.args[2]
        program_args = run_mock.call_args.args[3]
        additional_jars = run_mock.call_args.args[4]
        stdout = run_mock.call_args.args[5]
        stderr = run_mock.call_args.args[6]
        self.assertIsInstance(workspace, str)
        self.assertIsInstance(primary_endpoint, Endpoint)
        self.assertEqual(primary_endpoint.groupId, "mvxcvi")
        self.assertEqual(primary_endpoint.artifactId, "cljstyle")
        self.assertEqual(jvm_args, [])
        self.assertEqual(program_args, ["fix", "c:/path/to/file.clj"])
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)

    @patch("jgo.jgo._run")
    def test_program_arg_path_windows_sep(self, run_mock):
        parser = jgo_parser()
        argv = [
            "-r",
            "clojars=https://clojars.org/repo/",
            "mvxcvi:cljstyle",
            "fix",
            "c:\\path\\to\\file.clj",
        ]

        run(parser, argv)
        self.assertTrue(run_mock.called)
        workspace = run_mock.call_args.args[0]
        primary_endpoint: Endpoint = run_mock.call_args.args[1]
        jvm_args = run_mock.call_args.args[2]
        program_args = run_mock.call_args.args[3]
        additional_jars = run_mock.call_args.args[4]
        stdout = run_mock.call_args.args[5]
        stderr = run_mock.call_args.args[6]
        self.assertIsInstance(workspace, str)
        self.assertIsInstance(primary_endpoint, Endpoint)
        self.assertEqual(primary_endpoint.groupId, "mvxcvi")
        self.assertEqual(primary_endpoint.artifactId, "cljstyle")
        self.assertEqual(jvm_args, [])
        self.assertEqual(program_args, ["fix", "c:\\path\\to\\file.clj"])
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)

    @patch("jgo.jgo.launch_java")
    def test_explicit_main_class(self, launch_java_mock):
        parser = jgo_parser()
        argv = ["org.jruby:jruby-complete:@jruby.Main"]

        run(parser, argv)
        self.assertTrue(launch_java_mock.called)
        args, kwargs = _call_args(launch_java_mock)
        workspace = args[0]
        jvm_args = args[1]
        program_args = args[2:]
        additional_jars = kwargs["additional_jars"]
        stdout = kwargs["stdout"]
        stderr = kwargs["stderr"]
        check = kwargs["check"]
        self.assertIsInstance(workspace, str)
        self.assertEqual(jvm_args, [])
        self.assertEqual(program_args, ("org.jruby.Main",))
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)
        self.assertFalse(check)

    @patch("jgo.jgo.launch_java")
    def test_infer_main_class(self, launch_java_mock):
        parser = jgo_parser()
        argv = ["com.pinterest.ktlint:ktlint-cli"]

        run(parser, argv)
        self.assertTrue(launch_java_mock.called)
        args, kwargs = _call_args(launch_java_mock)
        workspace = args[0]
        jvm_args = args[1]
        program_args = args[2:]
        additional_jars = kwargs["additional_jars"]
        stdout = kwargs["stdout"]
        stderr = kwargs["stderr"]
        check = kwargs["check"]
        self.assertIsInstance(workspace, str)
        self.assertEqual(jvm_args, [])
        self.assertEqual(program_args, ("com.pinterest.ktlint.Main",))
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)
        self.assertFalse(check)


class TestUtil(unittest.TestCase):
    @patch("jgo.jgo._run")
    def test_main_from_endpoint(self, run_mock):
        main_from_endpoint(
            "org.janelia.saalfeldlab:paintera",
            argv=[],
            primary_endpoint_version="0.8.1",
            secondary_endpoints=("org.slf4j:slf4j-simple:1.7.25",),
        )

        self.assertTrue(run_mock.called)
        args, _ = _call_args(run_mock)
        workspace = args[0]
        primary_endpoint: Endpoint = args[1]
        jvm_args = args[2]
        program_args = args[3]
        additional_jars = args[4]
        stdout = args[5]
        stderr = args[6]
        self.assertIsInstance(workspace, str)
        self.assertIsInstance(primary_endpoint, Endpoint)
        self.assertEqual(primary_endpoint.groupId, "org.janelia.saalfeldlab")
        self.assertEqual(primary_endpoint.artifactId, "paintera")
        self.assertEqual(len(jvm_args), 2)
        self.assertIn("-Xmx", jvm_args[0])
        self.assertEqual(jvm_args[1], "-XX:+UseConcMarkSweepGC")
        self.assertEqual(program_args, [])
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)

        with open("{}/{}".format(workspace, "coordinates.txt")) as fh:
            coordinates = fh.read()

        self.assertIn("org.slf4j:slf4j-simple", coordinates)

    @patch("jgo.jgo._run")
    def test_main_from_endpoint_with_jvm_args(self, run_mock):
        main_from_endpoint(
            "org.janelia.saalfeldlab:paintera",
            argv=["-Xmx1024m", "--"],
            primary_endpoint_version="0.8.1",
            secondary_endpoints=("org.slf4j:slf4j-simple:1.7.25",),
        )

        self.assertTrue(run_mock.called)
        args, _ = _call_args(run_mock)
        workspace = args[0]
        primary_endpoint: Endpoint = args[1]
        jvm_args = args[2]
        program_args = args[3]
        additional_jars = args[4]
        stdout = args[5]
        stderr = args[6]
        self.assertIsInstance(workspace, str)
        self.assertIsInstance(primary_endpoint, Endpoint)
        self.assertEqual(primary_endpoint.groupId, "org.janelia.saalfeldlab")
        self.assertEqual(primary_endpoint.artifactId, "paintera")
        self.assertEqual(jvm_args, ["-Xmx1024m", "-XX:+UseConcMarkSweepGC"])
        self.assertEqual(program_args, [])
        self.assertEqual(additional_jars, [])
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)

        with open("{}/{}".format(workspace, "coordinates.txt")) as fh:
            coordinates = fh.read()

        self.assertIn("org.slf4j:slf4j-simple", coordinates)


class TestUtilMainCaughtExceptions(unittest.TestCase):
    def test_without_endpoint(self):
        rv = main_from_endpoint(
            "", argv=[], primary_endpoint_version="", secondary_endpoints=()
        )
        self.assertEqual(rv, 254, "Expected return code 254.")


if __name__ == "__main__":
    unittest.main()
