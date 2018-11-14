from distutils.core import setup

setup(
    name='jrun',
    version='0.1.0-dev',
    author='Philipp Hanslovsky',
    author_email='hanslovskyp@janelia.hhmi.org',
    description='Launch Java code from Python and the CLI, installation-free.',
    url='https://github.com/scijava/jrun',
    packages=['jrun'],
    entry_points={
        'console_scripts': [
            'jrun=jrun.jrun:jrun_main'
        ]
    },
    python_requires='>=3',
)
