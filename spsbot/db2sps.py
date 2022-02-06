#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# db2sps.py
# Description: automatically fills in data from a database in a spreadsheet
# -----------------------------------------------------------------------------
#
# Started on  <Tue Jul 24 15:17:58 2018 >
# -----------------------------------------------------------------------------
#
# Carlos Linares Lopez
# Login   <carlos.linares@uc3m.es>
#

"""
automatically fills in data from a database in a spreadsheet
"""


# imports
# -----------------------------------------------------------------------------
from . import preprocessor      # preprocessor of configuration files
from . import db2spsparser      # command-line parser
from . import spsparser         # spreadsheet parser
from . import utils

# globals
# -----------------------------------------------------------------------------

# default logger
LOGGER = utils.LOGGER

# info messages
INFO_PREPROCESSING = "Preprocessing ..."
INFO_PARSING = "Parsing ..."
INFO_PROCESSING = "Processing ..."

# main
#
# parses the command line and start a session to write data into the selected
# spreadsheet
# -----------------------------------------------------------------------------
def main():
    """parses the command line and start a session to write data into the selected
       spreadsheet"""

    # parse the command-line
    args = db2spsparser.DB2SPSParser().parse_args()

    # preprocess the configuration file
    LOGGER.info(INFO_PREPROCESSING)
    pragma = preprocessor.PRGProcessor(args.configuration)
    pragma.subst_templates()

    # create a database session and parse the output of the preprocessor
    LOGGER.info(INFO_PARSING)
    session = spsparser.VerbatimSPSParser()
    book = session.run(pragma.get_text())

    # now, create the sqlite3 database and writes data into it
    LOGGER.info(INFO_PROCESSING)
    book.execute(args.db, args.spreadsheet, args.sheetname, args.override)


# Main body
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    main()


# Local Variables:
# mode:python
# fill-column:80
# End:
