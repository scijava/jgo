from distutils.core import setup
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md')) as f:
    javarun_long_description = f.read()

setup(
    name='javarun',
    version='0.1.0-dev',
    author='Philipp Hanslovsky, Curtis Rueden',
    author_email='hanslovskyp@janelia.hhmi.org',
    description='Launch Java code from Python and the CLI, installation-free.',
    long_description=javarun_long_description,
    long_description_content_type='text/markdown',
    license='Public domain',
    url='https://github.com/scijava/jrun',
    packages=['javarun'],
    entry_points={
        'console_scripts': [
            'jrun=javarun.jrun:jrun_main'
        ]
    },
    python_requires='>=3',
)
