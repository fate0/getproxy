#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    'click>=6.0',
    'requests>=2.13.0',
    'gevent>=1.2.1',
    'geoip2>=2.5.0',
    'retrying>=1.3.3'
]

setup(
    name='getproxy',
    version='0.2.0',
    description="get proxy",
    long_description=readme,
    author="fate0",
    author_email='fate0@fatezero.org',
    url='https://github.com/fate0/getproxy',
    packages=find_packages(),
    package_dir={},
    entry_points={
        'console_scripts': [
            'getproxy=getproxy.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="BSD license",
    zip_safe=False,
    keywords='getproxy',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
