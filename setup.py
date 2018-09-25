from distutils.core import setup
from distutils.command.build_py import build_py

setup(
    name='jrun',
    version='0.1.0-dev',
    author='Philipp Hanslovsky',
    author_email='hanslovskyp@janelia.hhmi.org',
    description='jrun',
    url='https://github.com/ctrueden/jrun',
    packages=['jrun'],
    entry_points={
        'console_scripts': [
            'jrun=jrun.jrun:jrun_main'
        ]
    },
)
