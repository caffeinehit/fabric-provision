#!/usr/bin/env python
import provision
from setuptools import setup, find_packages

METADATA = dict(
    name='fabric-provision',
    version=provision.__version__,
    author='Alen Mujezinovic',
    author_email='alen@caffeinehit.com',
    description='Server provisioning with Chef',
    long_description=open('README.rst').read(),
    url='http://github.com/caffeinehit/fabric-provision',
    keywords='server provisioning fabric chef',
    install_requires=['fabric'],
    packages=find_packages(),
)

setup(**METADATA)
