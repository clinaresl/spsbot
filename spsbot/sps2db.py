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
from . import sps2dbparser      # command-line parser
from . import dbparser          # database parser


# main
#
# parses the command line and start a session to write data into the selected
# database
# -----------------------------------------------------------------------------
def main():
    """parses the command line and start a session to write data into the selected
       database"""

    # parse the command-line
    args = sps2dbparser.Sps2DBParser().parse_args()

    # create a database session and parse its contents
    session = dbparser.FileDBParser()
    database = session.run(args.configuration)

    # now, create the sqlite3 database and writes data into it
    database.create(args.db, args.append)
    database.insert(args.db, args.spreadsheet, args.sheetname, args.override, args.append)


# Main body
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    # run the main entry point
    main()


# Local Variables:
# mode:python
# fill-column:80
# End:
