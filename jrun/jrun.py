import argparse
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

# info() { test $verbose && echo "[INFO] $@"; }
# err() { echo "$@" 1>&2; }
# die() { err "$@"; exit 1; }

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
    print(java, cp, main_class)
    jvm_args = (jvm_args,) if jvm_args else tuple()
    return subprocess.run((java, '-cp', cp) + jvm_args + (main_class,) + app_args)

def run_and_combine_outputs(command, *args):
    return subprocess.check_output((command,) + args, stderr=subprocess.STDOUT)


def find_endpoint(argv):
    # endpoint is first positional argument
    for index, arg in enumerate(argv):
        if len(arg) > 0 and arg[0] != '-':
            return index
    return -1

def jrun_main():

    parser = argparse.ArgumentParser()

    try:
        run(parser)
    except subprocess.CalledProcessError as e:
        print("Error in {}: {}".format(e.cmd, e))
        print("Std out:")
        if e.stdout:
            for l in str(e.stdout).split('\\n'):
                print(l)
        if e.stderr:
            print("Std err:")
            for l in str(e.stderr).split('\\n'):
                print(l)
        parser.print_help()
        sys.exit(e.returncode)

    except NoMainClassInManifest as e:
        print(e)
        print("No main class given, and none found.")
        sys.exit(1)

def run(parser):

    argv = sys.argv[1:]

    
    endpoint_index = find_endpoint(argv)
    if endpoint_index == -1:
        return

    # expand endpoint here -- need to understand what @ctrueden does in his bash script
    # # G:A:V:C:mainClass
    endpoint         = Endpoint.parse_endpoint(argv[endpoint_index])
    jrun_and_jvm_ags = parser.parse_args(argv[:endpoint_index])

    config_file  = pathlib.Path(os.getenv('HOME')) / '.jrunrc'
    cache_dir    = pathlib.Path(os.getenv('HOME')) / '.jrun'
    m2_repo      = pathlib.Path (m2_path()) / 'repository'
    repositories = {
        'imagej'      : 'https://maven.imagej.net/content/groups/public',
        'saalfeldlab' : 'https://saalfeldlab.github.io/maven'
        }

    deps        = "<dependency>{}</dependency>".format(endpoint.dependency_string())
    repo_str    = ''.join('<repository><id>{rid}</id><url>{url}</url></repository>'.format(rid=k, url=v) for (k, v) in repositories.items())
    coordinates = endpoint.get_coordinates()
    workspace   = os.path.join(cache_dir, *(coordinates[0].split('.') + coordinates[1:]))
    main_class_file = os.path.join(workspace, endpoint.main_class, 'mainClass') if endpoint.main_class else os.path.join(workspace, 'mainClass')
    jar_dir     = None
    os.makedirs(workspace, exist_ok=True)

    try:
        with open(main_class_file, 'r') as f:
            main_class = f.readline()
        launch_java(workspace, '', main_class, *[])
        return
    except FileNotFoundError as e:
        pass

    

    maven_project ='''
<project>
	<modelVersion>4.0.0</modelVersion>
	<groupId>{groupId}-BOOTSTRAPPER</groupId>
	<artifactId>{artifactId}-BOOTSTRAPPER</artifactId>
	<version>0</version>
    <dependencies>{deps}</dependencies>
    <repositories>{repos}</repositories>
</project>
'''.format(
    groupId=endpoint.groupId,
    artifactId=endpoint.artifactId,
    deps=deps,
    repos=repo_str)
    pom_path = os.path.join(workspace, 'pom.xml')
    with open(pom_path, 'w') as f:
        f.write(maven_project)
    mvn_args = [] + ['-f', pom_path, 'dependency:resolve']

    mvn     = executable_path_or_raise('mvn')
    mvn_out = run_and_combine_outputs(mvn, *mvn_args)

    info_regex = re.compile('^.*\\[INFO\\] *')
    dependency_coordinates = []
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
                

            artifact_name = '-'.join((a, version, c) if c else (a, version))
            jar_file      = '{}.{}'.format(artifact_name, extension)

            try:
                link(os.path.join(m2_repo, *g.split('.'), a, version, jar_file), os.path.join(workspace, jar_file))
            except FileExistsError as e:
                # Do not throw exceptionif target file exists.
                pass

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

    os.makedirs(os.path.dirname(main_class_file), exist_ok=True)
    with open(main_class_file, 'w') as f:
        f.write(main_class)


    launch_java(workspace, '', main_class, *[])
    
    
    

