#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# sps2db.py
# Description: spreadsheet bot
# -----------------------------------------------------------------------------
#
# Started on  <Tue Jun 19 20:05:30 2018 >
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
reads data from a spreadsheet and writes it into a sqlite3 database
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.0'


# imports
# -----------------------------------------------------------------------------
import argparse                 # argument parsing
import fnmatch                  # Unix filename pattern matching
import os                       # os services
import sys                      # system accessing

import sps2dbparser             # command-line parser

import dbparser                 # database parser

# Main body
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    # parse the command-line
    cmdparser = sps2dbparser.Sps2DBParser ()
    args = cmdparser.parse_args ()

    # create a database session and parse its contents
    session = dbparser.FileDBParser ()
    database = session.run (args.configuration)

    # now, create the sqlite3 database and writes data into it
    database.create (args.db, args.append)
    database.insert (args.db, args.spreadsheet, args.sheetname, args.override, args.append)
    

# Local Variables:
# mode:python
# fill-column:80
# End:
