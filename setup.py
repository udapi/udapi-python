#!/usr/bin/env python3

from setuptools import setup, find_packages

# python_requires is supported by pip only from November 2016,
# so let's check the Python version also the old way.
import sys
if sys.version_info < (3, 3):
    raise SystemExit('Udapi requires Python 3.3 or higher.')

setup(
    name='udapi-python',
    version='0.2',
    description='Python framework for processing Universal Dependencies data',
    author='Martin Popel',
    author_email='popel@ufal.mff.cuni.cz',
    url='https://github.com/udapi/udapi-python',
    packages=find_packages(),
    scripts=['bin/udapy'],
    tests_require=['pytest'],
    install_requires=['colorama', 'termcolor', 'ufal.udpipe'],
    python_requires='>=3.3',
)
