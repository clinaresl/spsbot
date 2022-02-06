#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# utils.py
# Description: Helper functions
# -----------------------------------------------------------------------------
#
# Started on <jue 04-02-2021 21:28:18.019659815 (1612470498)>
# Carlos Linares López <carlos.linares@uc3m.es>
#

"""
Helper functions
"""

# imports
# -----------------------------------------------------------------------------
import logging
import os
import re

from . import colors

# constants
# -----------------------------------------------------------------------------

# logging

LOG_FORMAT = '[%(color_lvlname_prefix)s %(levelname)-8s:%(color_suffix)s %(color_ascitime_prefix)s %(asctime)s | %(color_suffix)s %(color_name_prefix)s %(name)s%(color_suffix)s]: %(color_prefix)s %(message)s %(color_suffix)s'
LOG_COLOR_PREFIX = {
    "ASCITIME" : colors.insert_prefix(foreground="#008080"),
    "NAME" : colors.insert_prefix(foreground="#00a0a0", italic=True),
    "DEBUG" : colors.insert_prefix(foreground="#99ccff"),
    "INFO" : colors.insert_prefix(foreground="#a0a020"),
    "WARNING" : colors.insert_prefix(foreground="#20aa20", bold=True),
    "ERROR" : colors.insert_prefix(foreground="#ff2020", bold=True),
    "CRITICAL" : colors.insert_prefix(foreground="#ff0000", bold=True)
}

#

# functions
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# get_basename
# return the basename of a file, i.e., the whole string but the contents after
# the *last* dot
# -----------------------------------------------------------------------------
def get_basename(filename: str):
    """return the basename of a file, i.e., the whole string but the contents after
       the *last* dot

    """

    # verify there is at least one dot
    match = re.match(r'(?P<filename>.*)\..*', filename)

    # if none exists, reeturn the whole string
    if not match:
        return filename

    # otherwise, just return everything before the last dot ---note this
    # function strongly relies on the greedy behaviour of the package re
    return match.group("filename")


# -----------------------------------------------------------------------------
# get_full_path
#
# return the absolute path of the path given in its argument which is expected
# to be a relative path which might use ~. This function does not implement any
# error checking. If the given string is badly-formed the results are undefined
# -----------------------------------------------------------------------------
def get_full_path(pathname: str):
    """return the absolute path of the path given in its argument which is expected
       to be a relative path which might use ~. This function does not implement
       any # error checking. If the given string is badly-formed the results are
       undefined

    """

    # remove unnecessary blanks
    pathname = pathname.strip()

    # in case the pathname is an absolute path. 'abspath' is used again to
    # ensure that the same convention is used regarding the inclusion of the
    # trailing os separator '/
    if os.path.isabs(pathname):
        return os.path.abspath(pathname)

    # in case this is a path starting with the $home. In this case, the first
    # component should be strictly equal to ~
    if pathname[0] == "~":

        # split the whole pathname into its components
        components = pathname.split(os.sep)

        # join all components again after expanding the first one
        pathname = os.path.join(os.path.expanduser("~"), *components[1:])

    # otherwise, this is assumed to be a relative path name so that return its
    # absolute path
    return os.path.abspath(pathname)

# -----------------------------------------------------------------------------
# get_filename
#
# return the right name of a file. If the given filename already finishes with
# the given suffix, then it is readily used; otherwise, the given suffix is
# added
# -----------------------------------------------------------------------------
def get_filename(filename: str, suffix: str):
    """return the right name of a file. If the given filename already finishes with
       the given suffix, then it is readily used; otherwise, the given suffix is
       added

    """

    # trivial case - no suffix is given
    if not suffix:
        return filename

    # break the filename into its different components
    split = os.path.splitext(filename)

    # before moving one make sure the specified suffix starts with a dot after
    # removing whitespaces at the beginning and end if any is given
    suffix = suffix.strip()
    suffix = '.' + suffix if suffix[0] != '.' else suffix

    # if the given suffix is already in use, then return the given filename
    # straight ahead
    if split[-1] == suffix:
        return filename

    # in any other case (either if no extension was given, or an extension
    # different than the specified suffix) was given, then add the given suffix
    return filename + suffix


# -----------------------------------------------------------------------------
# setup_logger
#
# setup and configure a logger
# -----------------------------------------------------------------------------
def setup_logger(verbose = False):
    """setup and configure a logger"""

    logger = logging.getLogger('spsbot')
    logger.addFilter(LoggerContextFilter())
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # and return the logger
    return logger


# -----------------------------------------------------------------------------
# LoggerContextFilter
#
# Creation of a context filter for the logger that adds color support
# -----------------------------------------------------------------------------
class LoggerContextFilter(logging.Filter):
    """
    Creation of a context filter for the logger that adds color support
    """

    def filter(self, record):

        # first inject the colors for all fields in the header
        record.color_lvlname_prefix = LOG_COLOR_PREFIX[record.levelname]
        record.color_ascitime_prefix = LOG_COLOR_PREFIX['ASCITIME']
        record.color_name_prefix = LOG_COLOR_PREFIX['NAME']

        # choose the color as a function of the level of the log message
        record.color_prefix = LOG_COLOR_PREFIX[record.levelname]
        record.color_suffix = colors.insert_suffix()

        return True

# globals
# -----------------------------------------------------------------------------

# default logger
LOGGER = setup_logger()


# Local Variables:
# mode:python
# fill-column:80
# End:
