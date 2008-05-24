#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

if "--setuptools" in sys.argv:
    sys.argv.remove("--setuptools")
    from setuptools import setup
    use_setuptools = True
else:
    from distutils.core import setup
    use_setuptools = False

DESCRIPTION = "nf3d is a visualization tools for Netfilter firewalls"
KEYWORDS = "network firewall"
REQUIRES = ("")

CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Natural Language :: English",
    "Environment :: Desktop",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python",
    "Topic :: System :: Monitoring"]

option = {}
if use_setuptools:
    option["zip_safe"] = True
    option["install_requires"] = REQUIRES

setup(
    name='nf3d',
    version='0.1',
    license='GPLv3',
    description=DESCRIPTION,
    classifiers=CLASSIFIERS,
    author="Eric Leblond",
    author_email="eric@inl.fr",
    keywords=KEYWORDS,
    packages=["nf3d"],
    platforms=['Linux'],
    package_dir={"nf3d"},
    scripts=["nf3d/nf3d"],
    **option)

