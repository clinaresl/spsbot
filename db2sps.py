#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# db2sps.py
# Description: automatically fills in data from a database in a spreadsheet
# -----------------------------------------------------------------------------
#
# Started on  <Tue Jul 24 15:17:58 2018 >
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
automatically fills in data from a database in a spreadsheet
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

import db2spsparser             # command-line parser

import spsparser                # spreadsheet parser

# Main body
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    # parse the command-line
    cmdparser = db2spsparser.DB2SPSParser ()
    args = cmdparser.parse_args ()

    # create a database session and parse its contents
    session = spsparser.FileSPSParser ()
    book = session.run (args.configuration)

    # now, create the sqlite3 database and writes data into it
    book.execute (args.db, args.spreadsheet, args.sheetname, args.override)
    


# Local Variables:
# mode:python
# fill-column:80
# End:
