#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2016 Óscar García Amor <ogarcia@connectical.com>
#
# Distributed under terms of the GNU GPLv3 license.

import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "vaultcli",
    version = "0.1.0",
    author = "Oscar Garcia Amor",
    author_email = "ogarcia@connectical.com",
    description = ("Awesome CLI for Vaultier"),
    license = "GPLv3",
    keywords = "cli vault web vaultier api easy",
    url = "https://github.com/telefonica/vaultier-cli",
    packages=['vaultcli'],
    long_description=read('README.md'),
    entry_points={
        'console_scripts': [
            'vaultcli = vaultcli.main:main'
        ]
    },
    install_requires = [
        "pycryptodomex>=3.4.3",
        "requests>=2.13.0",
        "colorama>=0.3.7",
        "tabulate>=0.7.7",
        "treelib>=1.3.5"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License (GPLv3)",
        'Programming Language :: Python :: 3',
    ],
)
