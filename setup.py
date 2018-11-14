from distutils.core import setup

setup(
    name='jgo',
    version='0.1.0-dev',
    author='Philipp Hanslovsky',
    author_email='hanslovskyp@janelia.hhmi.org',
    description='Launch Java code from Python and the CLI, installation-free.',
    url='https://github.com/scijava/jgo',
    packages=['jgo'],
    entry_points={
        'console_scripts': [
            'jgo=jgo.jgo:jgo_main'
        ]
    },
    python_requires='>=3',
)
