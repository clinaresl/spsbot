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
from . import db2spsparser      # command-line parser
from . import spsparser         # spreadsheet parser

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

    # create a database session and parse its contents
    session = spsparser.FileSPSParser()
    book = session.run(args.configuration)

    # now, create the sqlite3 database and writes data into it
    book.execute(args.db, args.spreadsheet, args.sheetname, args.override)


# Main body
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    main()


# Local Variables:
# mode:python
# fill-column:80
# End:
