from __future__ import absolute_import

from glob import glob
from os.path import basename, splitext
from setuptools import find_packages, setup

setup(
    name='game-job-search-tools',
    version='0.0.0',
    description="Game Job Search Tools",
    author='Pedro Boechat',
    author_email='pboechat@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    install_requires=['beautifulsoup4==4.6.0'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gamedevmap_report = gamedevmap.report:main'
        ]
    }
)
