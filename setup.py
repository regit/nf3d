#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright(C) 2008 Eric Leblond

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
"""

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
    packages=['nf3d'],
    package_dir={'nf3d':'nf3d'},
    package_data={'nf3d':['nf3dspec.conf']},
    scripts=['nf3d/nf3d'],
    **option)

