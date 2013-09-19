# -*- coding: utf-8 -*-
import sys
import os

from setuptools import setup, find_packages

def read(relative):
    contents = open(relative, 'r').read()
    return [l for l in contents.split('\n') if l != '']

setup(
    name='pyrox-stock',
    version=read('VERSION')[0],
    description='The stock filter package for Pyrox.',
    author='John Hopper',
    author_email='john.hopper@jpserver.net',
    url='https://github.com/zinic/pyrox-stock',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Cython',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: Internet',
        'Topic :: Utilities'
    ],
    tests_require=read('./etc/pip/tests-require.txt'),
    install_requires=read('./etc/pip/install-requires.txt'),
    test_suite='nose.collector',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=['*.tests']))
