#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# setup.py
# Description: spsbot setup file
# -----------------------------------------------------------------------------
#
# Login   <carlos.linares@uc3m.es>
#

"""
spsbot setup file
"""

# import sys
import setuptools

# import the version file
import spsbot.version

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name="spsbot",
    version=spsbot.version.__version__,
    author=spsbot.version.__author__,
    author_email=spsbot.version.__email__,
    description=spsbot.version.__description__,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/clinaresl/spsbot/",
    keywords="spreadsheet database sqlite3 ods csv xls",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "sps2db = spsbot.sps2db:main",
            "db2sps = spsbot.db2sps:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

# Local Variables:
# mode:python
# fill-column:80
# End:
