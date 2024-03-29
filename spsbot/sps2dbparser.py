#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# sps2dbparser.py
# Description: provides an argument parser for reading the argument command line
# of sps2db
# -----------------------------------------------------------------------------
#
# Started on  <Fri Jun 29 23:37:43 2018 >
# -----------------------------------------------------------------------------
#
# Carlos Linares Lopez
# Login   <carlos.linares@uc3m.es>
#

"""
provides an argument parser for reading the argument command line of sps2db
"""

# imports
# -----------------------------------------------------------------------------
import argparse                 # argument parsing
import sys                      # system accessing

from . import dbparser
from . import preprocessor
from . import version
from . import utils

# globals
# -----------------------------------------------------------------------------
LOGGER = utils.LOGGER

# -- info
INFO_CONF_GENERATED = "Configuration file '{0}' generated ..."

# -- errors
ERROR_NO_SPEC_FILE = "No database specification file! Make sure to invoke --parse-db/--show-templates/--generate-conf *after* --configuration"

# -----------------------------------------------------------------------------
# ShowDatabaseSpec
#
# shows a comprehensive output of the specification of the database
# -----------------------------------------------------------------------------
class ShowDatabaseSpec(argparse.Action):
    """
    shows a comprehensive output of the specification of the database
    """

    def __call__(self, parser, namespace, values, option_string=None):

        # if no test was provided, exit with a manual error
        if not namespace.configuration:
            parser.error(ERROR_NO_SPEC_FILE)
            sys.exit(0)

        # preprocess the configuration file
        pragma = preprocessor.PRGProcessor(namespace.configuration)
        pragma.subst_templates()

        # parse the contents of the configuration file after preprocessing it
        session = dbparser.VerbatimDBParser()
        database = session.run(pragma.get_text())

        # otherwise, process the file through the main entry point provided in
        # dbtools and exit
        print("""
 Contents of the database specification file:
 --------------------------------------------""")
        print(database)

        # and finally exit
        sys.exit(0)


# -----------------------------------------------------------------------------
# ShowTemplates
#
# shows a comprehensive output of all templates found in the configuration file
# -----------------------------------------------------------------------------
class ShowTemplates(argparse.Action):
    """shows a comprehensive output of all templates found in the configuration
    file

    """

    def __call__(self, parser, namespace, values, option_string=None):

        # if no test was provided, exit with a manual error
        if not namespace.configuration:
            parser.error(ERROR_NO_SPEC_FILE)
            sys.exit(0)

        # pre-process the configuration file
        pragma = preprocessor.PRGProcessor(namespace.configuration)
        pragma.subst_templates()

        # and show them on the standard output

        # otherwise, process the file through the main entry point provided in
        # dbtools and exit
        print("""
 Templates:
 --------------------------------------------
""")
        for itemplate in pragma:
            print(itemplate)
            print()

        # and finally exit
        sys.exit(0)


# -----------------------------------------------------------------------------
# GenerateConfFile
#
# generates a configuration file after applying all templates
# -----------------------------------------------------------------------------
class GenerateConfFile(argparse.Action):
    """generates a configuration file after applying all templates

    """

    def __call__(self, parser, namespace, values, option_string=None):

        # if no test was provided, exit with a manual error
        if not namespace.configuration:
            parser.error(ERROR_NO_SPEC_FILE)
            sys.exit(0)

        # pre-process the configuration file
        pragma = preprocessor.PRGProcessor(namespace.configuration)
        pragma.subst_templates()

        # and create the configuration file given in values to show the text
        # that results after performing all substitutions
        with open(values, 'w') as stream:
            stream.write(pragma.get_text())

        LOGGER.info(INFO_CONF_GENERATED.format(values))

        # and finally exit
        sys.exit(0)


# -----------------------------------------------------------------------------
# Sps2DBParser
#
# provides an argument parser for reading the argument command line of
# sps2db
# -----------------------------------------------------------------------------
class Sps2DBParser():
    """
    provides an argument parser for reading the argument command line of sps2db
    """

    def __init__(self):
        """
        create a parser and store its contents in this instance
        """

        # initialize a parser
        self._parser = argparse.ArgumentParser(description="Reads data from a spreadsheet and writes it into a sqlite3 database")

        # now, add the arguments

        # Group of mandatory arguments
        self._mandatory = self._parser.add_argument_group("Mandatory arguments", "The following arguments are required")
        self._mandatory.add_argument('-d', '--db',
                                     type=str,
                                     required=True,
                                     help="name of the output sqlite3 database. If a file exists with the same an error is raised")
        self._mandatory.add_argument('-c', '--configuration',
                                     type=str,
                                     required=True,
                                     help="location of the database specification file to use")

        # Group of optional arguments
        self._optional = self._parser.add_argument_group('Optional', 'The following arguments are optional')
        self._optional.add_argument('-s', '--spreadsheet',
                                    type=str,
                                    help="provides the location of the spreadsheet to read. If not given, the spreadsheet specified in the configuration file is used unless --override is given")
        self._optional.add_argument('-n', '--sheetname',
                                    type=str,
                                    help="if given, data is retrieved from the specified sheet name. If not given, the spreadsheet specified in the configuration file is used unless --override is given; if none is given neither here nor in the configuration file, the first sheet found in the spreadsheet is used by default")
        self._optional.add_argument('-o', '--override',
                                    default=False,
                                    action='store_true',
                                    help="if given, the spreadsheet and the sheetname specified with --spreadsheet and --sheetname are used even if others are found in the configuration file")
        self._optional.add_argument('-a', '--append',
                                    default=False,
                                    action='store_true',
                                    help="if given, all data extracted from the spreadsheet is added to the specified database tables; if not, an error is raised in case a database table with the same name is found. In any case, if a database with the same name given with --db exists, execution halts")

        # Group of miscellaneous arguments
        self._misc = self._parser.add_argument_group('Miscellaneous')
        self._misc.add_argument('-b', '--parse-db',
                                nargs=0,
                                action=ShowDatabaseSpec,
                                help="processes the database specification file, shows the resulting definitions and exits")
        self._misc.add_argument('-t', '--show-templates',
                                nargs=0,
                                action=ShowTemplates,
                                help="shows all templates found in the configuration file on the standard output after making all the necessary substitutions")
        self._misc.add_argument('-g', '--generate-conf',
                                action=GenerateConfFile,
                                help="generates a configuration file after applying all templates")
        self._misc.add_argument('-q', '--quiet',
                                action='store_true',
                                help="suppress headers")
        self._misc.add_argument('-V', '--version',
                                action='version',
                                version=" %s version %s (%s)" % (sys.argv[0],
                                                                 version.__version__,
                                                                 version.__revision__),
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
