#!/usr/bin/env python
from setuptools import setup, find_packages

METADATA = dict(
    name='fabric-provision',
    version='0.0.4',
    author='Alen Mujezinovic',
    author_email='alen@caffeinehit.com',
    description='Server provisioning with Chef',
    long_description=open('README.rst').read(),
    url='http://github.com/caffeinehit/fabric-provision',
    keywords='server provisioning fabric chef',
    install_requires=['fabric>=1.1'],
    packages=find_packages(),
)

setup(**METADATA)
