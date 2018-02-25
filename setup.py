# coding=utf-8
from setuptools import find_packages
from setuptools import setup

setup(
    name='code_fixers',
    description='Some out-of-the-box hooks for pre-commit.',
    url='https://github.com/pre-commit/pre-commit-hooks',
    version='1.0.0',

    author='Vikram Arsid',
    author_email='vikramarsid@gmail.com',

    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],

    packages=find_packages(exclude=('tests*', 'testing*')),
    install_requires=[
        'pre-commit'
    ],
    entry_points={
        'console_scripts': [
            'error_number_fixer = error_number_fixer.src.error_number_fixer:main',
            'check_added_plugin_files = check_added_plugin_files.src.check_added_plugin_files:main'
        ],
    },
)
