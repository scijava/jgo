from distutils.core import setup

setup(
    name='javarun',
    version='0.1.0-dev',
    author='Philipp Hanslovsky',
    author_email='hanslovskyp@janelia.hhmi.org',
    description='Launch Java code from Python and the CLI, installation-free.',
    url='https://github.com/scijava/jrun',
    packages=['javarun'],
    entry_points={
        'console_scripts': [
            'jrun=javarun.jrun:jrun_main'
        ]
    },
    python_requires='>=3',
)
