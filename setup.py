#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='udapi',
    version='0.2.3',
    description='Python framework for processing Universal Dependencies data',
    long_description=(
      'Udapi is an open-source framework providing API for processing '
      'Universal Dependencies data. It is available in Python, Perl and Java. '
      'Udapi is suitable both for full-fledged applications and fast '
      'prototyping: visualization of dependency trees, format conversions, '
      'querying, editing and transformations, validity tests, dependency '
      'parsing, evaluation etc.'
    ),
    author='Martin Popel',
    author_email='popel@ufal.mff.cuni.cz',
    url='https://github.com/udapi/udapi-python',
    packages=find_packages(),
    scripts=['bin/udapy'],
    tests_require=['pytest'],
    install_requires=['colorama', 'termcolor'],
    python_requires='>=3.6',
    license='GPL 2 or newer',
    platforms='any',
)
