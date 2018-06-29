#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# sps2dbparser.py
# Description: provides an argument parser for reading the argument command line of sps2db
# -----------------------------------------------------------------------------
#
# Started on  <Fri Jun 29 23:37:43 2018 >
# Last update <sábado, 21 diciembre 2013 02:14:41 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id::                                                                      $
# $Date::                                                                    $
# $Revision::                                                                $
# -----------------------------------------------------------------------------
#
# Made by 
# Login   <clinares@atlas>
#

"""
provides an argument parser for reading the argument command line of sps2db
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.0'


# imports
# -----------------------------------------------------------------------------
import argparse                 # argument parsing
import sys                      # system accessing

import dbparser


# -----------------------------------------------------------------------------
# ShowDatabaseSpec
#
# shows a comprehensive output of the specification of the database
# -----------------------------------------------------------------------------
class ShowDatabaseSpec (argparse.Action):
    """
    shows a comprehensive output of the specification of the database
    """

    def __call__(self, parser, namespace, values, option_string=None):

        # if no test was provided, exit with a manual error
        if not namespace.configuration:
            parser.error (" no database specification file! Make sure to invoke --parse-db *after* --configuration")
            sys.exit (0)

        # parse the database
        session = dbparser.FileDBParser ()
        database = session.run (namespace.configuration)
            
        # otherwise, process the file through the main entry point provided in
        # dbtools and exit
        print ("""
 Contents of the database specification file:
 --------------------------------------------""")
        print(database)

        # and finally exit
        sys.exit (0)


# -----------------------------------------------------------------------------
# Sps2DBParser
#
# provides an argument parser for reading the argument command line of
# sps2db
# -----------------------------------------------------------------------------
class Sps2DBParser (object):
    """
    provides an argument parser for reading the argument command line of sps2db
    """

    def __init__ (self):
        """
        create a parser and store its contents in this instance
        """

        # initialize a parser
        self._parser = argparse.ArgumentParser (description="Reads data from a spreadsheet and writes it into a sqlite3 database")

        # now, add the arguments

        # Group of mandatory arguments
        self._mandatory = self._parser.add_argument_group ("Mandatory arguments", "The following arguments are required")
        self._mandatory.add_argument ('-s', '--spreadsheet',
                                      type=str,
                                      required=True,
                                      help="provides the location of the spreadsheet to read")
        self._mandatory.add_argument ('-d', '--db',
                                      type=str,
                                      required=True,
                                      help="name of the output sqlite3 database")
        self._mandatory.add_argument ('-c', '--configuration',
                                      type=str,
                                      required=True,
                                      help="location of the database specification file to use")

        # Group of optional arguments
        self._optional = self._parser.add_argument_group ('Optional', 'The following arguments are optional')
        self._optional.add_argument ('-n', '--sheetname',
                                     type=str,
                                     help="if given, data is retrieved from the specified sheet name; otherwise, the first sheet is used by default")

        # Group of miscellaneous arguments
        self._misc = self._parser.add_argument_group ('Miscellaneous')
        self._misc.add_argument ('-b', '--parse-db',
                                 nargs=0,
                                 action=ShowDatabaseSpec,
                                 help="processes the database specification file, shows the resulting definitions and exits")
        self._misc.add_argument ('-q', '--quiet',
                                 action='store_true',
                                 help="suppress headers")
        self._misc.add_argument ('-V', '--version',
                                 action='version',
                                 version=" %s version %s" % (sys.argv [0], __version__),
                                 help="output version information and exit")

    # -----------------------------------------------------------------------------
    # parse_args
    #
    # just parse the arguments with this argument parser
    # -----------------------------------------------------------------------------
    def parse_args (self):
        """
        just parse the arguments with this argument parser
        """

        return self._parser.parse_args ()



# Local Variables:
# mode:python
# fill-column:80
# End:
