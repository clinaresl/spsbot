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
import db2spsparser             # command-line parser

import spsparser                # spreadsheet parser

# Main body
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    # parse the command-line
    CMDPARSER = db2spsparser.DB2SPSParser()
    ARGS = CMDPARSER.parse_args()

    # create a database session and parse its contents
    SESSION = spsparser.FileSPSParser()
    BOOK = SESSION.run(ARGS.configuration)

    # now, create the sqlite3 database and writes data into it
    BOOK.execute(ARGS.db, ARGS.spreadsheet, ARGS.sheetname, ARGS.override)


# Local Variables:
# mode:python
# fill-column:80
# End:
