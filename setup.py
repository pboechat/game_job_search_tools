from __future__ import absolute_import

from setuptools import setup

setup(
    name='game-job-search-tools',
    version='0.0.0',
    description="Game Job Search Tools",
    author='Pedro Boechat',
    author_email='pboechat@gmail.com',
    package_dir={'': 'src'},
    py_modules=['gamedevmap_report'],
    install_requires=['beautifulsoup4==4.6.0'],
    entry_points={
        'console_scripts': [
            'gamedevmap_report = gamedevmap_report:main'
        ]
    }
)
