#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='udapi-python',
    version='0.1',
    description='Python framework for processing Universal Dependencies data',
    author='Vincent Kriz',
    author_email='kriz@ufal.mff.cuni.cz',
    url='https://github.com/udapi/udapi-python',
    packages=find_packages(),
    scripts=['bin/udapy'],
    tests_require=['pytest'],
)
