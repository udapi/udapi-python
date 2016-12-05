#!/usr/bin/env python

from distutils.core import setup

setup(
    name='Udapi-Python',
    version='0.1',
    description='Python framework for processing Universal Dependencies data',
    author='Vincent Kriz',
    author_email='kriz@ufal.mff.cuni.cz',
    url='https://github.com/udapi/udapi-python',
    packages=['udapi'],
    scripts=['bin/udapy']
)
