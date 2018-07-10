import argparse
import configparser
import glob
import os
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

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

class NoMainClassInManifest(Exception):
    def __init__(self, jar):
        super(NoMainClassInManifest, self).__init__('{} manifest does not specify Main-Class'.format(jar))
        self.jar = jar

class ExecutableNotFound(Exception):
    def __init__(self, executable, path):
        super(ExecutableNotFound, self).__init__('{} not found on path {}',format(executable, path))

class InvalidEndpoint(Exception):
    def __init__(self, endpoint, reason):
        super(InvalidEndpoint, self).__init__('Invalid endpoint {}: {}'.format(endpoint, reason))
        self.endpoint = endpoint
        self.reason   = reason

class UnableToAutoComplete(Exception):
    def __init__(self, clazz):
        super(UnableToAutoComplete, self).__init__('Unable to auto-complete {}'.format(clazz))
        self.clazz = clazz

class HelpRequested(Exception):
    def __init__(self, argv):
        super(HelpRequested, self).__init__('Help requested {}'.format(argv))
        self.argv = argv

class NoEndpointProvided(Exception):
    def __init__(self, argv):
        super(NoEndpointProvided, self).__init__('No endpoint found in provided arguments: {}'.format(argv))
        self.argv = argv

class Endpoint():

    VERSION_RELEASE = "RELEASE"
    VERSION_LATEST  = "LATEST"
    
    def __init__(
            self,
            groupId,
            artifactId,
            version=VERSION_RELEASE,
            classifier=None,
            main_class=None):
        super(Endpoint, self).__init__()
        self.groupId    = groupId
        self.artifactId = artifactId
        self.version    = version
        self.classifier = classifier
        self.main_class = main_class

    def jar_name(self):
        return '-'.join(([self.artifactId, self.classifier] if self.classifier else [self.artifactId]) + [self.version]) + '.jar'

    def dependency_string(self):
        xml = '<groupId>{groupId}</groupId><artifactId>{artifactId}</artifactId><version>{version}</version>'.format(
            groupId    = self.groupId,
            artifactId = self.artifactId,
            version    = self.version
            )
        if (self.classifier):
            xml = xml + '<classifier>{classifier}</classifier>'.format(classifier=self.classifier)
        return xml

    def get_coordinates(self):
        return [self.groupId, self.artifactId, self.version] + ([self.classifier] if self.classifier else [])


    def is_endpoint(string):
        endpoint_elements = string.split(':')

        if len(endpoint_elements) < 2 or len(endpoint_elements) > 5:
            return False

        return True

    def parse_endpoint(endpoint):
        # G:A:V:C:mainClass
        endpoint_elements = endpoint.split(':')
        endpoint_elements_count = len(endpoint_elements)

        if (endpoint_elements_count > 5):
            raise InvalidEndpoint(endpoint, 'Too many elements.')

        if (endpoint_elements_count < 2):
            raise InvalidEndpoint(endpoint, 'Not enough artifacts specified.')

        if (endpoint_elements_count == 4):
            return Endpoint(*endpoint_elements[:3], main_class=endpoint_elements[3])

        if (endpoint_elements_count == 3):
            if re.match('({})|({})|({})'.format('[0-9].*', Endpoint.VERSION_RELEASE, Endpoint.VERSION_LATEST), endpoint_elements[2]):
                return Endpoint(*endpoint_elements[:2], version=endpoint_elements[2])
            else:
                return Endpoint(*endpoint_elements[:2], main_class=endpoint_elements[2])

        return Endpoint(*endpoint_elements)
        

def executable_path_or_raise(tool):
    path = executable_path(tool)
    if path is None:
        raise ExecutableNotFound(tool, os.getenv('PATH'))
    return path

def executable_path(tool):
    return shutil.which(tool)

def link(source, link_name, link_type="hard"):
    if link_type.lower() == "soft":
        os.symlink(source, linke_name)
    elif link_type.lower() == "hard":
        os.link(source, link_name)
    else:
        shutil.copyfile(source, link_name)

def m2_path():
    return os.getenv("M2_REPO", (pathlib.Path(os.getenv('HOME')) / '.m2').absolute())

def expand(string, **shortcuts):

    for (k, v) in shortcuts.items():
        if string in k:
            return '{}{}'.format(v, )

    return string

def launch_java(
        jar_dir,
        jvm_args,
        main_class,
        *app_args
        ):
    java = executable_path('java')
    if not java:
        raise ExecutableNotFound('java', os.getenv('PATH'))
    cp = os.path.join(jar_dir, '*')
    jvm_args = (jvm_args,) if jvm_args else tuple()
    return subprocess.run((java, '-cp', cp) + jvm_args + (main_class,) + app_args)

def run_and_combine_outputs(command, *args):
    return subprocess.check_output((command,) + args, stderr=subprocess.STDOUT)


def find_endpoint(argv, shortcuts={}):
    # endpoint is first positional argument
    pattern = re.compile('.*https?://.*')
    for index, arg in enumerate(argv):
        if arg in shortcuts or (Endpoint.is_endpoint(arg) and not pattern.match(arg)):
            return index
    return -1

def jrun_main(argv=sys.argv[1:]):

    epilog='''
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

Multiple artifacts can be concatenated with pluses,
and all of them will be included on the classpath.
However, you should not specify multiple main classes.
'''

    parser = argparse.ArgumentParser(
        description     = 'Run Java main class from maven coordinates.',
        usage           = '%(prog)s [-v] [-u] [-U] [-m] [JVM_OPTIONS [JVM_OPTIONS ...]] <endpoint> [main-args]',
        epilog          = epilog,
        formatter_class = argparse.RawTextHelpFormatter
    )
    parser.add_argument('-v', '--verbose', action='count', help='verbose mode flag', default=0)
    parser.add_argument('-u', '--update-cache', action='store_true', help='update/regenerate cached environment')
    parser.add_argument('-U', '--force-update', action='store_true', help='force update from remote Maven repositories (implies -u)')
    parser.add_argument('-m', '--manage-dependencies', action='store_true', help='use endpoints for dependency management (see "Details" below)')
    parser.add_argument('-r', '--repository', nargs='+', help='Add additional maven repository (key=url format)', default=[], required=False)


    try:
        run(parser, argv=argv)
    except subprocess.CalledProcessError as e:
        print("Error in {}: {}".format(e.cmd, e), file=sys.stderr)
        print("Std out:", file=sys.stderr)
        if e.stdout:
            for l in str(e.stdout).split('\\n'):
                print(l, file=sys.stderr)
        if e.stderr:
            print("Std err:", file=sys.stderr)
            for l in str(e.stderr).split('\\n'):
                print(l, file=sys.stderr)
        parser.print_help(file=sys.stderr)
        sys.exit(e.returncode)

    except NoMainClassInManifest as e:
        print(e, file=sys.stderr)
        print("No main class given, and none found.", file=sys.stderr)
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    except HelpRequested as e:
        parser.parse_known_args(e.argv)

    except Exception as e:
        print(e, file=sys.stderr)
        parser.print_help(file=sys.stderr)
        sys.exit(1)

def default_config():
    config = configparser.ConfigParser()

    # settings
    config.add_section('settings')
    config.set('settings', 'm2Repo', os.path.join(os.getenv('HOME'), '.m2', 'repository'))
    config.set('settings', 'cacheDir', os.path.join(os.getenv('HOME'), '.jrun'))
    config.set('settings', 'links', 'hard')

    # repositories
    config.add_section('repositories')

    # shortcuts
    config.add_section('shortcuts')

    return config

def expand_coordinate(coordinate, shortcuts={}):
    if coordinate in shortcuts:
        coordinate = shortcuts[coordinate]
        was_changed = True

    split = coordinate.split(':')
    for i, s in enumerate(split):
        if s in shortcuts:
            split[i] = shortcuts[s]
    coordinate = ':'.join(split)
    return coordinate

def autocomplete_main_class(main_class, artifactId, workspace):
    main_class = main_class.replace('/', '.')
    jar_cmd    = executable_path_or_raise('jar')
    args       = ('tf',)

    if main_class[0] == '@':
        format_str    = '.*{}\\.class'.format(main_class[1:])
        pattern       = re.compile(format_str)
        relevant_jars = [jar for jar in glob.glob(os.path.join(workspace, '*.jar')) if artifactId in os.path.basename(jar)]
        for jar in relevant_jars:
            out = subprocess.check_output((jar_cmd,) + args + (jar,))
            for line in out.decode('utf-8').split('\n'):
                line = line.strip()
                if pattern.match(line):
                    return line[:-6].replace('/','.')
        raise UnableToAutoComplete(main_class)

    return main_class

def resolve_dependencies(
        endpoint,
        cache_dir,
        m2_repo,
        update_cache=False,
        force_update=False,
        manage_dependencies=False,
        repositories={},
        shortcuts={},
        verbose=0):

    update_cache = True if force_update else update_cache

    endpoint    = endpoint if isinstance(endpoint, Endpoint) else Endpoint.parse_endpoint(expand_coordinate(endpoint, shortcuts=shortcuts))
    deps        = "<dependency>{}</dependency>".format(endpoint.dependency_string())
    repo_str    = ''.join('<repository><id>{rid}</id><url>{url}</url></repository>'.format(rid=k, url=v) for (k, v) in repositories.items())
    coordinates = endpoint.get_coordinates()
    workspace   = os.path.join(cache_dir, *(coordinates[0].split('.') + coordinates[1:]))

    if manage_dependencies:
        dependency_management = '<dependency><groupId>{g}</groupId><artifactId>{a}</artifactId><version>{v}</version>'.format(
            g=endpoint.groupId,
            a=endpoint.artifactId,
            v=endpoint.version)
        if endpoint.classifier:
            dependency_management += '<classifier>{c}</classifier>'.format(c=endpoint.classifier)
        dependency_management += '<type>pom</type><scope>import</scope></dependency>'

    else:
        dependency_management = ''

    maven_project ='''
<project>
	<modelVersion>4.0.0</modelVersion>
	<groupId>{groupId}-BOOTSTRAPPER</groupId>
	<artifactId>{artifactId}-BOOTSTRAPPER</artifactId>
	<version>0</version>
	<dependencyManagement>
		<dependencies>{depMgmt}</dependencies>
	</dependencyManagement>
	<dependencies>{deps}</dependencies>
	<repositories>{repos}</repositories>
</project>
'''.format(
    groupId=endpoint.groupId,
    artifactId=endpoint.artifactId,
    depMgmt=dependency_management,
    deps=deps,
    repos=repo_str)
    pom_path = os.path.join(workspace, 'pom.xml')
    with open(pom_path, 'w') as f:
        f.write(maven_project)
    mvn_args = ['-B'] \
               + ['-f', pom_path, 'dependency:resolve'] \
               + (['-U'] if force_update else []) \
               + (['-X'] if verbose > 1 else [])

    try:
        mvn     = executable_path_or_raise('mvn')
        mvn_out = run_and_combine_outputs(mvn, *mvn_args)
    except subprocess.CalledProcessError as e:
        print( "Failed to bootstrap the artifact.", file=sys.stderr)
        print( "", file=sys.stderr)
        print( "Possible solutions:", file=sys.stderr)
        print("* Double check the endpoint for correctness (https://search.maven.org/).", file=sys.stderr)
        print("* Add needed repositories to ~/.jrunrc [repositories] block (see README).", file=sys.stderr)
        print("* Try with an explicit version number (release metadata might be wrong).", file=sys.stderr)
        print('', file=sys.stderr)
        raise e


    info_regex = re.compile('^.*\\[[A-Z]+\\] *')
    relevant_jars = []
    for l in str(mvn_out).split('\\n'):
        if re.match('.*:(compile|runtime)', l):
            split_line     = info_regex.sub('', l).split(':')
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
                

            artifact_name         = '-'.join((a, version, c) if c else (a, version))
            jar_file              = '{}.{}'.format(artifact_name, extension)
            jar_file_in_workspace = os.path.join(workspace, jar_file)

            relevant_jars.append(jar_file_in_workspace)

            try:
                link(os.path.join(m2_repo, *g.split('.'), a, version, jar_file), jar_file_in_workspace)
            except FileExistsError as e:
                # Do not throw exceptionif target file exists.
                pass
    return relevant_jars


def run(parser, argv=sys.argv[1:]):

    config_file = pathlib.Path(os.getenv('HOME')) / '.jrunrc'
    config      = default_config()
    config.read(config_file)

    settings     = config['settings']
    repositories = config['repositories']
    shortcuts    = config['shortcuts']

    endpoint_index = find_endpoint(argv, shortcuts)
    if endpoint_index == -1:
        raise HelpRequested(argv) if '-h' in argv or '--help' in argv else NoEndpointProvided(argv)

    args, unknown = parser.parse_known_args(argv[:endpoint_index])
    jvm_args      = ' '.join(unknown) if unknown else ''
    program_args  = [] if endpoint_index == -1 else argv[endpoint_index+1:]

    cache_dir    = settings.get('cacheDir')
    m2_repo      = settings.get('m2Repo')
    for repository in args.repository:
        repositories[repository.split('=')[0]] = repository.split('=')[1]

    if args.force_update:
        args.update_cache = True

    endpoint        = Endpoint.parse_endpoint(expand_coordinate(argv[endpoint_index], shortcuts=shortcuts))
    deps            = "<dependency>{}</dependency>".format(endpoint.dependency_string())
    repo_str        = ''.join('<repository><id>{rid}</id><url>{url}</url></repository>'.format(rid=k, url=v) for (k, v) in repositories.items())
    coordinates     = endpoint.get_coordinates()
    workspace       = os.path.join(cache_dir, *(coordinates[0].split('.') + coordinates[1:]))
    main_class_file = os.path.join(workspace, endpoint.main_class, 'mainClass') if endpoint.main_class else os.path.join(workspace, 'mainClass')

    if args.update_cache:
        shutil.rmtree(workspace, True)

    os.makedirs(workspace, exist_ok=True)

    try:
        with open(main_class_file, 'r') as f:
            main_class = f.readline()
        launch_java(workspace, jvm_args, main_class, *program_args)
        return
    except FileNotFoundError as e:
        pass

    relevant_jars = resolve_dependencies(
        endpoint,
        cache_dir           = cache_dir,
        m2_repo             = m2_repo,
        update_cache        = args.update_cache,
        force_update        = args.force_update,
        manage_dependencies = args.manage_dependencies,
        repositories        = repositories,
        shortcuts           = shortcuts,
        verbose             = args.verbose)

    if args.verbose > 0:
        print("Relevant jars", relevant_jars)

    if not endpoint.main_class:
        jar_path = glob.glob(os.path.join(workspace, endpoint.jar_name()).replace(Endpoint.VERSION_RELEASE, '*').replace(Endpoint.VERSION_LATEST, '*'))[0]
        with zipfile.ZipFile(jar_path) as jar_file:
            with jar_file.open('META-INF/MANIFEST.MF') as manifest:
                main_class_pattern = re.compile('.*Main-Class: *')
                main_class         = None
                for line in manifest.readlines():
                    line = line.strip().decode('utf-8')
                    if main_class_pattern.match(line):
                        main_class = main_class_pattern.sub('', line)
                        break
        if not main_class:
            raise NoMainClassInManifest(jar_path)
    else:
        main_class = endpoint.main_class

    main_class = autocomplete_main_class(main_class, endpoint.artifactId, workspace)

    os.makedirs(os.path.dirname(main_class_file), exist_ok=True)
    with open(main_class_file, 'w') as f:
        f.write(main_class)


    launch_java(workspace, jvm_args, main_class, *program_args)
    
    
    

