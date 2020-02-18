#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# sps2db.py
# Description: spreadsheet bot
# -----------------------------------------------------------------------------
#
# Started on  <Tue Jun 19 20:05:30 2018 >
# -----------------------------------------------------------------------------
#
# Carlos Linares Lopez
# Login   <carlos.linares@uc3m.es>
#

"""
reads data from a spreadsheet and writes it into a sqlite3 database
"""

# imports
# -----------------------------------------------------------------------------
import sps2dbparser             # command-line parser

import dbparser                 # database parser

# Main body
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    # parse the command-line
    CMDPARSER = sps2dbparser.Sps2DBParser()
    ARGS = CMDPARSER.parse_args()

    # create a database session and parse its contents
    SESSION = dbparser.FileDBParser()
    DATABASE = SESSION.run(ARGS.configuration)

    # now, create the sqlite3 database and writes data into it
    DATABASE.create(ARGS.db, ARGS.append)
    DATABASE.insert(ARGS.db, ARGS.spreadsheet, ARGS.sheetname, ARGS.override, ARGS.append)



# Local Variables:
# mode:python
# fill-column:80
# End:
