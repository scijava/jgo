import argparse
import configparser
import glob
import logging
import os
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile
import hashlib

# A script to execute a main class of a Maven artifact
# which is available locally or from Maven Central.
#
# Works using the maven-dependency-plugin to stash the artifact
# and its deps to a temporary location, then invokes java.
#
# It would be more awesome to enhance the exec-maven-plugin to support
# running something with a classpath built from the local Maven repository
# cache. Then you would get all the features of exec-maven-plugin.
# But this script works in a pinch for simple cases.

# Define some useful functions.

_classpath_separator = ";" if os.name == "nt" else ":"

_logger = logging.getLogger(os.getenv("JRUN_LOGGER_NAME", "jgo"))


def classpath_separator():
    return _classpath_separator


class NoMainClassInManifest(Exception):
    def __init__(self, jar):
        super(NoMainClassInManifest, self).__init__(
            "{} manifest does not specify Main-Class".format(jar)
        )
        self.jar = jar


class ExecutableNotFound(Exception):
    def __init__(self, executable, path):
        super(ExecutableNotFound, self).__init__(
            "{} not found on path {}".format(executable, path)
        )


class InvalidEndpoint(Exception):
    def __init__(self, endpoint, reason):
        super(InvalidEndpoint, self).__init__(
            "Invalid endpoint {}: {}".format(endpoint, reason)
        )
        self.endpoint = endpoint
        self.reason = reason


class UnableToAutoComplete(Exception):
    def __init__(self, clazz):
        super(UnableToAutoComplete, self).__init__(
            "Unable to auto-complete {}".format(clazz)
        )
        self.clazz = clazz


class HelpRequested(Exception):
    def __init__(self, argv):
        super(HelpRequested, self).__init__("Help requested {}".format(argv))
        self.argv = argv


class NoEndpointProvided(Exception):
    def __init__(self, argv):
        super(NoEndpointProvided, self).__init__(
            "No endpoint found in provided arguments: {}".format(argv)
        )
        self.argv = argv


class Endpoint:

    VERSION_RELEASE = "RELEASE"
    VERSION_LATEST = "LATEST"
    VERSION_MANAGED = "MANAGED"

    def __init__(
        self,
        groupId,
        artifactId,
        version=VERSION_RELEASE,
        classifier=None,
        main_class=None,
    ):
        super(Endpoint, self).__init__()
        self.groupId = groupId
        self.artifactId = artifactId
        self.version = version
        self.classifier = classifier
        self.main_class = main_class

    def __repr__(self):
        return f"<jgo.Endpoint:g={self.groupId},a={self.artifactId},v={self.version},c={self.classifier},main={self.main_class}>"

    def jar_name(self):
        return (
            "-".join(
                (
                    [self.artifactId, self.classifier]
                    if self.classifier
                    else [self.artifactId]
                )
                + [self.version]
            )
            + ".jar"
        )

    def dependency_string(self):
        xml = (
            "<groupId>{groupId}</groupId><artifactId>{artifactId}</artifactId>".format(
                groupId=self.groupId, artifactId=self.artifactId
            )
        )
        if self.version != Endpoint.VERSION_MANAGED:
            xml += "<version>{version}</version>".format(version=self.version)
        if self.classifier:
            xml = xml + "<classifier>{classifier}</classifier>".format(
                classifier=self.classifier
            )
        return xml

    def get_coordinates(self):
        return (
            [self.groupId, self.artifactId]
            + ([self.version] if self.version != Endpoint.VERSION_MANAGED else [])
            + ([self.classifier] if self.classifier else [])
        )

    def is_endpoint(string):
        endpoint_elements = (
            string.split("+")[0].split(":") if "+" in string else string.split(":")
        )

        if (
            len(endpoint_elements) < 2
            or len(endpoint_elements) > 5
            or endpoint_elements[0].startswith("-")
        ):
            return False

        return True

    def parse_endpoint(endpoint):
        # G:A:V:C:mainClass
        endpoint_elements = endpoint.split(":")
        endpoint_elements_count = len(endpoint_elements)

        if endpoint_elements_count > 5:
            raise InvalidEndpoint(endpoint, "Too many elements.")

        if endpoint_elements_count < 2:
            raise InvalidEndpoint(endpoint, "Not enough artifacts specified.")

        if endpoint_elements_count == 4:
            return Endpoint(*endpoint_elements[:3], main_class=endpoint_elements[3])

        if endpoint_elements_count == 3:
            if re.match(
                "({})|({})|({})|({})".format(
                    "[0-9a-f].*",
                    Endpoint.VERSION_RELEASE,
                    Endpoint.VERSION_LATEST,
                    Endpoint.VERSION_MANAGED,
                ),
                endpoint_elements[2],
            ):
                return Endpoint(*endpoint_elements[:2], version=endpoint_elements[2])
            else:
                return Endpoint(*endpoint_elements[:2], main_class=endpoint_elements[2])

        return Endpoint(*endpoint_elements)

    def remove_main_class(self):
        self.main_class = None
        return self


def executable_path_or_raise(tool):
    path = executable_path(tool)
    if path is None:
        raise ExecutableNotFound(tool, os.getenv("PATH"))
    return path


def executable_path(tool):
    return shutil.which(tool)


def link(source, link_name, link_type="auto"):
    _logger.debug(
        "Linking source %s to target %s with link_type %s", source, link_name, link_type
    )
    if link_type.lower() == "soft":
        return os.symlink(source, link_name)
    elif link_type.lower() == "hard":
        return os.link(source, link_name)
    elif link_type.lower() == "copy":
        return shutil.copyfile(source, link_name)
    elif link_type.lower() == "auto":
        try:
            return link(source=source, link_name=link_name, link_type="hard")
        except OSError as e:
            if e.errno != 18:
                raise e
        try:
            return link(source=source, link_name=link_name, link_type="soft")
        except OSError:
            pass

        return link(source=source, link_name=link_name, link_type="copy")

    raise Exception(
        "Unable to link source {} to target {} with link_type {}",
        source,
        link_name,
        link_type,
    )


def m2_path():
    return os.getenv("M2_REPO", (pathlib.Path.home() / ".m2").absolute())


def launch_java(
    jar_dir,
    jvm_args,
    main_class,
    *app_args,
    additional_jars=[],
    stdout=None,
    stderr=None,
    **subprocess_run_kwargs,
):
    java = executable_path("java")
    if not java:
        raise ExecutableNotFound("java", os.getenv("PATH"))

    cp = classpath_separator().join([os.path.join(jar_dir, "*")] + additional_jars)
    _logger.debug("class path: %s", cp)
    jvm_args = tuple(arg for arg in jvm_args) if jvm_args else tuple()
    return subprocess.run(
        (java, "-cp", cp) + jvm_args + (main_class,) + app_args,
        stdout=stdout,
        stderr=stderr,
        **subprocess_run_kwargs,
    )


def run_and_combine_outputs(command, *args):
    command_string = (command,) + args
    _logger.debug(f"Executing: {command_string}")
    return subprocess.check_output(command_string, stderr=subprocess.STDOUT)


_default_log_levels = (
    "NOTSET",
    "DEBUG",
    "INFO",
    "WARN",
    "ERROR",
    "CRITICAL",
    "FATAL",
    "TRACE",
)


class CustomArgParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._found_unknown_hyphenated_args = False
        self._found_endpoint = False
        self._found_optionals = []

    def _match_arguments_partial(self, actions, arg_strings_pattern):
        # Doesnt support --additional-endpoints yet
        result = []
        args_after_double_equals = len(arg_strings_pattern.partition("-")[2])
        for i, arg_string in enumerate(self._found_optionals):
            if Endpoint.is_endpoint(arg_string):
                rv = [
                    i,
                    1,
                    len(self._found_optionals) - i - 1 + args_after_double_equals,
                ]
                return rv
        return result

    def _parse_optional(self, arg_string):
        if arg_string.startswith("-") and arg_string not in self._option_string_actions:
            self._found_unknown_hyphenated_args = True
        elif Endpoint.is_endpoint(arg_string):
            self._found_endpoint = True

        if self._found_unknown_hyphenated_args or self._found_endpoint:
            self._found_optionals.append(arg_string)
            return None

        rv = super()._parse_optional(arg_string)
        return rv

    def error(self, message):
        if message == "the following arguments are required: <endpoint>":
            raise NoEndpointProvided([])


def jgo_parser(log_levels=_default_log_levels):
    usage = (
        "usage: jgo [-v] [-u] [-U] [-m] [-q] [--log-level] [--ignore-jgorc]\n"
        "           [--link-type type] [--additional-jars jar [jar ...]]\n"
        "           [--additional-endpoints endpoint [endpoint ...]]\n"
        "           [JVM_OPTIONS [JVM_OPTIONS ...]] <endpoint> [main-args]"
    )
    epilog = """
The endpoint should have one of the following formats:

- groupId:artifactId
- groupId:artifactId:version
- groupId:artifactId:mainClass
- groupId:artifactId:version:mainClass
- groupId:artifactId:version:classifier:mainClass

If version is omitted, then RELEASE is used.
If mainClass is omitted, it is auto-detected.
You can also write part of a class beginning with an @ sign,
and it will be auto-completed.
"""

    parser = CustomArgParser(
        prog="jgo",
        description="Run Java main class from Maven coordinates.",
        usage=usage[len("usage: ") :],
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose", action="count", help="verbose mode flag", default=0
    )
    parser.add_argument(
        "-u",
        "--update-cache",
        action="store_true",
        help="update/regenerate cached environment",
    )
    parser.add_argument(
        "-U",
        "--force-update",
        action="store_true",
        help="force update from remote Maven repositories (implies -u)",
    )
    parser.add_argument(
        "-m",
        "--manage-dependencies",
        action="store_true",
        help='use endpoints for dependency management (see "Pitfalls")',
    )
    parser.add_argument(
        "-r",
        "--repository",
        nargs="+",
        help="Add additional Maven repository (key=url format)",
        default=[],
        required=False,
    )
    parser.add_argument(
        "-a",
        "--additional-jars",
        nargs="+",
        help="Add additional jars to classpath",
        default=[],
        required=False,
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        required=False,
        help="Suppress jgo output, including logging",
    )
    parser.add_argument(
        "--additional-endpoints",
        nargs="+",
        help="Add additional endpoints",
        default=[],
        required=False,
    )
    parser.add_argument("--ignore-jgorc", action="store_true", help="Ignore ~/.jgorc")
    parser.add_argument(
        "--link-type",
        default=None,
        type=str,
        help="How to link from local Maven repository into jgo cache.\n"
        + "Defaults to the `links' setting in ~/.jgorc or 'auto' if not specified.",
        choices=("hard", "soft", "copy", "auto"),
    )
    parser.add_argument(
        "--log-level", default=None, type=str, help="Set log level", choices=log_levels
    )
    parser.add_argument(
        "jvm_args",
        help="JVM arguments",
        metavar="jvm-args",
        nargs="*",
        default=[],
    )
    parser.add_argument(
        "endpoint",
        help="Endpoint",
        metavar="<endpoint>",
    )
    parser.add_argument(
        "program_args",
        help="Program arguments",
        metavar="main-args",
        nargs="*",
        default=[],
    )

    return parser


def _jgo_main(argv=sys.argv[1:], stdout=None, stderr=None):

    LOG_FORMAT = "%(levelname)s %(asctime)s: %(message)s"

    if not ("-q" in argv or "--quiet" in argv):
        logging.basicConfig(
            level=logging.INFO,
            # datefmt = '%Y-%m-%d -  %H:%M:%S',
            format=LOG_FORMAT,
        )

    parser = jgo_parser()

    try:
        completed_process = run(parser, argv=argv, stdout=stdout, stderr=stderr)
        completed_process.check_returncode()

    except HelpRequested:
        parser.print_help()

    except NoEndpointProvided:
        parser.print_usage()
        _logger.error(
            "No endpoint provided. Run `jgo --help' for a detailed help message."
        )
        return 254

    except subprocess.CalledProcessError as e:
        return e.returncode

    return 0


def jgo_cache_dir_environment_variable():
    return "JGO_CACHE_DIR"


def default_config():
    config = configparser.ConfigParser()

    # settings
    config.add_section("settings")
    config.set(
        "settings",
        "m2Repo",
        os.path.join(str(pathlib.Path.home()), ".m2", "repository"),
    )
    config.set("settings", "cacheDir", os.path.join(str(pathlib.Path.home()), ".jgo"))
    config.set("settings", "links", "auto")

    # repositories
    config.add_section("repositories")

    # shortcuts
    config.add_section("shortcuts")

    return config


def expand_coordinate(coordinate, shortcuts={}):
    was_changed = True
    used_shortcuts = set()
    while was_changed:
        matched_shortcut = False
        for shortcut, replacement in shortcuts.items():
            if shortcut not in used_shortcuts and coordinate.startswith(shortcut):
                _logger.debug(
                    "Replacing %s with %s in %s.", shortcut, replacement, coordinate
                )
                coordinate = coordinate.replace(shortcut, replacement)
                matched_shortcut = True
                used_shortcuts.add(shortcut)
        was_changed = matched_shortcut

    _logger.debug("Returning expanded coordinate %s.", coordinate)
    return coordinate


def autocomplete_main_class(main_class, artifactId, workspace):
    main_class = main_class.replace("/", ".")
    jar_cmd = executable_path_or_raise("jar")
    args = ("tf",)

    if main_class[0] == "@":
        format_str = ".*{}\\.class".format(main_class[1:])
        pattern = re.compile(format_str)
        relevant_jars = [
            jar
            for jar in glob.glob(os.path.join(workspace, "*.jar"))
            if artifactId in os.path.basename(jar)
        ]
        for jar in relevant_jars:
            out = subprocess.check_output((jar_cmd,) + args + (jar,))
            for line in out.decode("utf-8").split("\n"):
                line = line.strip()
                if pattern.match(line):
                    return line[:-6].replace("/", ".")
        raise UnableToAutoComplete(main_class)

    return main_class


def split_endpoint_string(endpoint_string):
    endpoint_strings = endpoint_string.split("+")
    endpoint_strings = endpoint_strings[0:1] + sorted(endpoint_strings[1:])
    return endpoint_strings


def endpoints_from_strings(endpoint_strings, shortcuts={}):
    return [
        Endpoint.parse_endpoint(expand_coordinate(ep, shortcuts=shortcuts))
        for ep in endpoint_strings
    ]


def coordinates_from_endpoints(endpoints):
    return [ep.get_coordinates() for ep in endpoints]


def workspace_dir_from_coordinates(coordinates, cache_dir):
    coord_string = "+".join(["-".join(c) for c in coordinates])
    hash_path = hashlib.sha256(coord_string.encode("utf-8")).hexdigest()
    workspace = os.path.join(cache_dir, *coordinates[0], hash_path)

    return workspace


def workspace_dir_from_endpoint_strings(
    endpoint_strings, cache_dir, shortcuts={}
):  # pragma: no cover
    """Unused"""
    if isinstance(endpoint_strings, str):
        return workspace_dir_from_endpoint_strings(
            split_endpoint_string(endpoint_strings)
        )

    endpoints = endpoints_from_strings(endpoint_strings)
    coordinates = coordinates_from_endpoints(endpoints)
    return workspace_dir_from_coordinates(coordinates, cache_dir)


def resolve_dependencies(
    endpoint_string,
    cache_dir,
    m2_repo,
    link_type="auto",
    update_cache=False,
    force_update=False,
    manage_dependencies=False,
    repositories={},
    shortcuts={},
    verbose=0,
):

    endpoint_strings = split_endpoint_string(endpoint_string)
    endpoints = endpoints_from_strings(endpoint_strings, shortcuts=shortcuts)
    primary_endpoint = endpoints[0]
    deps = "".join(
        "<dependency>{}</dependency>".format(ep.dependency_string()) for ep in endpoints
    )
    repo_str = "".join(
        "<repository><id>{rid}</id><url>{url}</url></repository>".format(rid=k, url=v)
        for (k, v) in repositories.items()
    )
    coordinates = coordinates_from_endpoints(endpoints)
    workspace = workspace_dir_from_coordinates(coordinates, cache_dir=cache_dir)
    build_success_file = os.path.join(workspace, "buildSuccess")

    update_cache = True if force_update else update_cache
    update_cache = (
        update_cache
        or not os.path.isdir(workspace)
        or not os.path.isfile(build_success_file)
    )

    if not update_cache:
        return primary_endpoint, workspace

    _logger.info(
        "First time start-up may be slow. "
        "Downloaded dependencies will be cached "
        "for shorter start-up times in subsequent executions."
    )

    if update_cache:
        shutil.rmtree(workspace, True)

    os.makedirs(workspace, exist_ok=True)

    # Write a file with the coordinates into the workspace dir
    with open(os.path.join(workspace, "coordinates.txt"), "w") as f:
        for coordinate in coordinates:
            f.write("".join([":".join(coordinate)] + ["\n"]))

    # TODO should this be for all endpoints or only the primary endpoint?
    if manage_dependencies:
        if primary_endpoint.version == Endpoint.VERSION_MANAGED:
            raise InvalidEndpoint(
                primary_endpoint, "A primary endpoint cannot also be version=MANAGED."
            )
        dependency_management = "<dependency><groupId>{g}</groupId><artifactId>{a}</artifactId><version>{v}</version>".format(
            g=primary_endpoint.groupId,
            a=primary_endpoint.artifactId,
            v=primary_endpoint.version,
        )
        if primary_endpoint.classifier:
            dependency_management += "<classifier>{c}</classifier>".format(
                c=primary_endpoint.classifier
            )
        dependency_management += "<type>pom</type><scope>import</scope></dependency>"

    else:
        dependency_management = ""

    maven_project = """
<project>
\t<modelVersion>4.0.0</modelVersion>
\t<groupId>{groupId}-BOOTSTRAPPER</groupId>
\t<artifactId>{artifactId}-BOOTSTRAPPER</artifactId>
\t<version>0</version>
\t<dependencyManagement>
\t\t<dependencies>{depMgmt}</dependencies>
\t</dependencyManagement>
\t<dependencies>{deps}</dependencies>
\t<repositories>{repos}</repositories>
</project>
""".format(
        groupId=primary_endpoint.groupId,
        artifactId=primary_endpoint.artifactId,
        depMgmt=dependency_management,
        deps=deps,
        repos=repo_str,
    )
    pom_path = os.path.join(workspace, "pom.xml")
    os.makedirs(workspace, exist_ok=True)
    with open(pom_path, "w") as f:
        f.write(maven_project)
    mvn_args = (
        ["-B"]
        + ["-f", pom_path, "dependency:resolve"]
        + (["-U"] if force_update else [])
        + (["-X"] if verbose > 1 else [])
    )

    try:
        mvn = executable_path_or_raise("mvn")
        mvn_out = run_and_combine_outputs(mvn, *mvn_args)
    except subprocess.CalledProcessError as e:
        _logger.error("Failed to bootstrap the artifact.")
        _logger.error("")

        _logger.error("Possible solutions:")
        _logger.error(
            "* Double check the endpoint for correctness (https://search.maven.org/)."
        )
        _logger.error(
            "* Add needed repositories to ~/.jgorc [repositories] block (see README)."
        )
        _logger.error(
            "* Try with an explicit version number (release metadata might be wrong)."
        )
        _logger.error("")
        _logger.error("Full Maven error output:")
        err_lines = []
        if e.stdout:
            err_lines += e.stdout.decode().splitlines()
        if e.stderr:
            err_lines += e.stderr.decode().splitlines()
        for l in err_lines:
            if l.startswith("[ERROR]"):
                _logger.error("\t%s", l)
            else:
                _logger.debug("\t%s", l)
        _logger.error("")

        raise e

    info_regex = re.compile("^.*\\[[A-Z]+\\] *")
    relevant_jars = []
    for l in str(mvn_out).split("\\n"):
        # TODO: the compile|runtime|provided matches might fail if an artifactId starts with accordingly
        # TODO: If that ever turns out to be an issue, it is going to be necessary to update these checks
        if (
            re.match(".*:(compile|runtime)", l)
            and not re.match(".*\\[DEBUG\\]", l)
            and not re.match(".*:provided", l)
        ):

            _logger.debug("Relevant mvn output: %s", l)

            split_line = info_regex.sub("", l).split(":")
            split_line_len = len(split_line)

            if split_line_len < 5 and split_line_len > 6:
                continue

            if split_line_len == 6:
                # G:A:P:C:V:S
                (g, a, extension, c, version, scope) = split_line
            elif split_line_len == 5:
                # G:A:P:V:S
                (g, a, extension, version, scope) = split_line
                c = None

            artifact_name = "-".join((a, version, c) if c else (a, version))
            jar_file = "{}.{}".format(artifact_name, extension)
            jar_file_in_workspace = os.path.join(workspace, jar_file)

            relevant_jars.append(jar_file_in_workspace)

            try:
                link(
                    os.path.join(m2_repo, *g.split("."), a, version, jar_file),
                    jar_file_in_workspace,
                    link_type=link_type,
                )
            except FileExistsError:
                # Do not throw exception if target file exists.
                pass
    pathlib.Path(build_success_file).touch(exist_ok=True)
    return primary_endpoint, workspace


def run(parser, argv=sys.argv[1:], stdout=None, stderr=None):

    config = default_config()
    if not "--ignore-jgorc" in argv:
        config_file = pathlib.Path.home() / ".jgorc"
        config.read(config_file)

    if os.getenv(jgo_cache_dir_environment_variable()) is not None:
        cache_dir = os.getenv(jgo_cache_dir_environment_variable())
        _logger.debug("Setting cache dir from environment: %s", cache_dir)
        config.set("settings", "cacheDir", cache_dir)

    settings = config["settings"]
    repositories = config["repositories"]
    shortcuts = config["shortcuts"]

    if "-h" in argv or "--help" in argv:
        raise HelpRequested(argv)

    args = parser.parse_args(argv)

    if not args.endpoint:
        raise NoEndpointProvided(argv)
    if args.endpoint in shortcuts and not Endpoint.is_endpoint(args.endpoint):
        raise NoEndpointProvided(argv)

    jvm_args = args.jvm_args
    program_args = args.program_args
    if args.log_level:
        logging.getLogger().setLevel(logging.getLevelName(args.log_level))

    if args.additional_jars is not None and len(args.additional_jars) > 0:
        _logger.warning(
            "The -a, --additional-jars option has been deprecated and will be removed in the future. "
            "Please use `mvn install:install-file' instead to make relevant JARS available in your "
            "local Maven repository and pass appropriate coordinates as endpoints."
        )

    if args.verbose > 0:
        _logger.setLevel(logging.DEBUG)

    if args.link_type is not None:
        config.set("settings", "links", args.link_type)

    cache_dir = settings.get("cacheDir")
    m2_repo = settings.get("m2Repo")
    link_type = settings.get("links")
    for repository in args.repository:
        repositories[repository.split("=")[0]] = repository.split("=")[1]

    _logger.debug("Using settings:     %s", dict(settings))
    _logger.debug("Using repositories: %s", dict(repositories))
    _logger.debug("Using shortcuts:    %s", dict(shortcuts))

    if args.force_update:
        args.update_cache = True

    endpoint_string = "+".join([args.endpoint] + args.additional_endpoints)

    primary_endpoint, workspace = resolve_dependencies(
        endpoint_string,
        cache_dir=cache_dir,
        m2_repo=m2_repo,
        update_cache=args.update_cache,
        force_update=args.force_update,
        manage_dependencies=args.manage_dependencies,
        repositories=repositories,
        shortcuts=shortcuts,
        verbose=args.verbose,
        link_type=link_type,
    )
    return _run(
        workspace,
        primary_endpoint,
        jvm_args,
        program_args,
        args.additional_jars,
        stdout,
        stderr,
    )


def _run(
    workspace, primary_endpoint, jvm_args, program_args, additional_jars, stdout, stderr
):
    main_class_file = (
        os.path.join(workspace, primary_endpoint.main_class)
        if primary_endpoint.main_class
        else os.path.join(workspace, "mainClass")
    )
    try:
        with open(main_class_file, "r") as f:
            main_class = f.readline()
        return launch_java(
            workspace,
            jvm_args,
            main_class,
            *program_args,
            additional_jars=additional_jars,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    except FileNotFoundError:
        pass

    if not primary_endpoint.main_class:
        _logger.info("Inferring main class from jar manifest")
        jar_path = glob.glob(
            os.path.join(workspace, primary_endpoint.jar_name())
            .replace(Endpoint.VERSION_RELEASE, "*")
            .replace(Endpoint.VERSION_LATEST, "*")
        )[0]
        with zipfile.ZipFile(jar_path) as jar_file:
            with jar_file.open("META-INF/MANIFEST.MF") as manifest:
                main_class_pattern = re.compile(".*Main-Class: *")
                main_class = None
                for line in manifest.readlines():
                    line = line.strip().decode("utf-8")
                    if main_class_pattern.match(line):
                        main_class = main_class_pattern.sub("", line)
                        break
        if not main_class:
            raise NoMainClassInManifest(jar_path)
        _logger.info("Inferred main class: %s", main_class)
    else:
        main_class = primary_endpoint.main_class

    main_class = autocomplete_main_class(
        main_class, primary_endpoint.artifactId, workspace
    )

    os.makedirs(os.path.dirname(main_class_file), exist_ok=True)
    with open(main_class_file, "w") as f:
        f.write(main_class)

    return launch_java(
        workspace,
        jvm_args,
        main_class,
        *program_args,
        additional_jars=additional_jars,
        stdout=stdout,
        stderr=stderr,
        check=False,
    )
