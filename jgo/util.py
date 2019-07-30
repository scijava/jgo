import psutil
import sys

from .jgo import _jgo_main as main

def add_jvm_args_as_necessary(argv, gc_option='-XX:+UseConcMarkSweepGC'):
    """

    Extend existing ``argv`` with reasonable default values for garbage collection and max heap size.
    If ``-Xmx`` is not specified in ``argv``, set max heap size to half the system's memory.

    :param argv: arugment vector
    :param gc_option: Use this garbage collector settings, if any.
    :return: ``argv`` with
    """
    if gc_option and not gc_option in argv:
        argv += [gc_option]

    for arg in argv:
        if '-Xmx' in arg:
            return argv

    total_memory  = psutil.virtual_memory().total
    exponent      = 3 if total_memory > 2*1024**3 else 2
    memory_unit   = 'G' if exponent == 3 else 'M'
    max_heap_size = '{}{}'.format(max(total_memory // (1024**exponent) // 2, 1), memory_unit)

    argv = ['-Xmx{}'.format(max_heap_size)] + argv

    return argv

def maven_scijava_repository():
    return 'https://maven.scijava.org/content/groups/public'


def main_from_endpoint(
        primary_endpoint,
        argv=sys.argv[1:],
        repositories={'scijava.public': maven_scijava_repository()},
        primary_endpoint_version=None,
        primary_endpoint_main_class=None,
        secondary_endpoints=()):
    """
    Convenience method to populate appropriate argv for jgo. This is useful to distribute Java programs as Python modules.

    For example, to run paintera with slf4j logging bindings, call
    ``
    main_from_endpoint(
        'org.janelia.saalfeldlab:paintera',
        primary_endpoint_version='0.8.1',
        secondary_endpoints=('org.slf4j:slf4j-simple:1.7.25',),
    )
    ``

    :param primary_endpoint: The primary endpoint of the Java program you want to run.
    :param repositories: Any maven repository that holds the required jars. Defaults to {'scijava.public': maven_scijava_repository()}.
    :param primary_endpoint_version: Will be appended to ``primary_endpoint`` if it does not evaluate to ``False``
    :param primary_endpoint_main_class: Will be appended to ``primary_endpoitn`` if it does not evaluate to ``False``.
    :param secondary_endpoints: Any other endpoints that should be added.
    :return: ``None``
    """
    double_dash_index  = [i for (i, arg) in enumerate(argv) if arg == '--'][0] if '--' in argv else -1
    jgo_and_jvm_argv   = ([] if double_dash_index < 0 else argv[:double_dash_index]) + ['--ignore-jgorc']
    repository_strings = ['-r'] + ['{}={}'.format(k, v) for (k, v) in repositories.items()]
    primary_endpoint   = primary_endpoint + ':{}'.format(primary_endpoint_version) if primary_endpoint_version else primary_endpoint
    primary_endpoint   = primary_endpoint + ':{}'.format(primary_endpoint_main_class) if primary_endpoint_main_class else primary_endpoint
    endpoint           = ['+'.join((primary_endpoint,) + secondary_endpoints)]
    paintera_argv      = argv if double_dash_index < 0 else argv[double_dash_index+1:]
    argv               = add_jvm_args_as_necessary(jgo_and_jvm_argv) + repository_strings + endpoint + paintera_argv

    main(argv=argv)
