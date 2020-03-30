#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# db2spsparser.py
# Description: provides an argument parser for reading the argument
# command line of db2sps
# -----------------------------------------------------------------------------
#
# Started on  <Tue Jul 24 15:18:45 2018 >
# -----------------------------------------------------------------------------
#
# Carlos Linares Lopez
# Login   <carlos.linares@uc3m.es>
#

"""
provides an argument parser for reading the argument command line of db2sps
"""

# imports
# -----------------------------------------------------------------------------
import argparse                 # argument parsing
import sys                      # system accessing

from . import spsparser
from . import version

# -----------------------------------------------------------------------------
# ShowDatabaseSpec
#
# shows a comprehensive output of the specification of the spreadsheet
# -----------------------------------------------------------------------------
class ShowDatabaseSpec(argparse.Action):
    """
    shows a comprehensive output of the specification of the spreadsheet
    """

    def __call__(self, parser, namespace, values, option_string=None):

        # if no test was provided, exit with a manual error
        if not namespace.configuration:
            parser.error(" no spreadsheet specification file! Make sure to invoke --parse-sps *after* --configuration")
            sys.exit(0)

        # parse the database
        session = spsparser.FileSPSParser()
        book = session.run(namespace.configuration)

        # otherwise, process the file through the main entry point provided in
        # dbtools and exit
        print("""
 Contents of the spreadsheet specification file:
 --------------------------------------------""")
        print(book)

        # and finally exit
        sys.exit(0)


# -----------------------------------------------------------------------------
# DB2SPSParser
#
# provides an argument parser for reading the argument command line of
# db2sps
# -----------------------------------------------------------------------------
class DB2SPSParser():
    """
    provides an argument parser for reading the argument command line of db2sps
    """

    def __init__(self):
        """
        create a parser and store its contents in this instance
        """

        # initialize a parser
        self._parser = argparse.ArgumentParser(description="automatically fills in data from a database in a spreadsheet")

        # now, add the arguments

        # Group of mandatory arguments
        self._mandatory = self._parser.add_argument_group("Mandatory arguments", "The following arguments are required")
        self._mandatory.add_argument('-c', '--configuration',
                                     type=str,
                                     required=True,
                                     help="location of the spreadsheet specification file to use")

        # Group of optional arguments
        self._optional = self._parser.add_argument_group('Optional', 'The following arguments are optional')
        self._optional.add_argument('-d', '--db',
                                    type=str,
                                    help="name of the input sqlite3 database")
        self._optional.add_argument('-s', '--spreadsheet',
                                    type=str,
                                    help="filename of the spreadsheet to write. If not given, the spreadsheet specified in the configuration file is used unless --override is given")
        self._optional.add_argument('-n', '--sheetname',
                                    type=str,
                                    help="if given, data is written to the specified sheet name. If not given, the spreadsheet specified in the configuration file is used unless --override is given; if none is given neither here nor in the configuration file, a default sheet is created automatically")
        self._optional.add_argument('-o', '--override',
                                    default=False,
                                    action='store_true',
                                    help="if given, the database, the spreadsheet and the sheetname specified with --db, --spreadsheet and --sheetname are used even if others are found in the configuration file")

        # Group of miscellaneous arguments
        self._misc = self._parser.add_argument_group('Miscellaneous')
        self._misc.add_argument('-b', '--parse-sps',
                                nargs=0,
                                action=ShowDatabaseSpec,
                                help="processes the spreadsheet specification file, shows the resulting definitions and exits")
        self._misc.add_argument('-q', '--quiet',
                                action='store_true',
                                help="suppress headers")
        self._misc.add_argument('-V', '--version',
                                action='version',
                                version=" %s version %s (%s)" % \
                                (sys.argv[0], version.__version__, version.__revision__),
                                help="output version information and exit")

    # -----------------------------------------------------------------------------
    # parse_args
    #
    # just parse the arguments with this argument parser
    # -----------------------------------------------------------------------------
    def parse_args(self):
        """
        just parse the arguments with this argument parser
        """

        return self._parser.parse_args()



# Local Variables:
# mode:python
# fill-column:80
# End:
