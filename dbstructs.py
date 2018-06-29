#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dbstructs.py
# Description: Definition of all classes required to represent the
# information parsed from a db file
# -----------------------------------------------------------------------------
# Login   <clinares@atlas>
#

"""Definition of all classes required to represent the information
parsed from a db file

"""



# globals
# -----------------------------------------------------------------------------
__version__  = '1.0'


# imports
# -----------------------------------------------------------------------------
import math                             # pow
import re                               # match
import sys                              # exit

import pyexcel
import sqlite3


# functions
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# get_columnrow
#
# return a tuple (column, row) represented with a string and an integer
# -----------------------------------------------------------------------------
def get_columnrow (cellname):
    '''return a tuple (column, row) represented with a string and an integer'''

    # extract the column and the row from the given cell name
    m = re.match (r'(?P<column>[a-zA-Z]+)(?P<row>\d+)', cellname)

    # and make sure to cast the row to an integer
    return (m.groups ()[0], int (m.groups () [1]))


# -----------------------------------------------------------------------------
# get_columnindex
#
# return a unique integer identifier for the given column which is
# represented as a string. For this, characters are translate into
# numbers and the whole sequence is interpreted as a number in base 26
# -----------------------------------------------------------------------------
def get_columnindex (columnname):
    '''return a unique integer identifier for the given column which is
       represented as a string. For this, characters are translated
       into numbers and the whole sequence is interpreted as a number
       in base 26

    '''

    # first, convert each character in the given row into a number
    # just by substracting the ordinal of character 'A' and adding 1
    # to avoid zeroes. For this, make sure that the given column is
    # interpreted as an upper case letter.
    intcol = [1 + ord (x.upper ()) - ord ('A') for x in columnname]

    # Next, process this number in base 26 (which is the value of 1 +
    # ord ('Z') - ord ('A'))
    result = 0
    for index, icolumn in enumerate (intcol):
        result += icolumn * math.pow (1 + ord ('Z') - ord ('A'), len (intcol) - index - 1)

    # and return the result, base zero
    return int (result) - 1


# -----------------------------------------------------------------------------
# get_index
#
# return a unique integer identifier for the given cell (represented
# with a column which is a string and a row which is a number) given
# that it belongs to a region which contains precisely nbrows and
# whose first row is index startrow
# -----------------------------------------------------------------------------
def get_index (cellname, startrow, nbrows):

    '''return a unique integer identifier for the given cell (represented
       with a column which is a string and a row which is a number)
       given that it belongs to a region which contains precisely
       nbrows and whose first row is index startrow

    '''

    # first, extract the column and row from the cellname 
    column, row = get_columnrow (cellname)
    
    # apply the typical formula - note that this index starts
    # assigning values from column 'A'
    return get_columnindex (column) * nbrows + (row - startrow)


# -----------------------------------------------------------------------------
# get_columnname
#
# returns the string representing the column whose index is the given one
# -----------------------------------------------------------------------------
def get_columnname (columnindex):
    '''returns the string representing the column whose index is the given
       one

    '''

    # initialization
    pos = 0                                     # compute digits upwards
    result = str()                              # starting with the empty str

    base = 1 + ord ('Z') - ord ('A')            # yeah, 26 ... obviously?
    while True:

        # compute this digit as the remainder with the base of the next position
        digit = int ( ( columnindex % int (math.pow (base, 1 + pos)) ) / math.pow (base, pos) )

        # there is a caveat here. If the value is promoted to an upper
        # position, it can not be zero in general, of course. However,
        # in lexicographic order, the upper value can be 'A' (which is
        # the equivalent of zero)
        if not pos:
            result = chr ( ord ('A') + digit) + result
        else:
            result = chr ( ord ('A') + digit - 1) + result

        # substract the amount we just computed
        columnindex -= digit * int (math.pow (base, pos))

        # and go to the next upper location
        pos += 1

        # until we exhausted the index
        if columnindex == 0:
            break

    # and return the result
    return result
    

# -----------------------------------------------------------------------------
# get_cellname
#
# return a cell represented with a string (column) and an integer
# (row) whose index is the given one provided that it belongs to a
# region with nbrows in total which starts at startrow
# -----------------------------------------------------------------------------
def get_cellname (index, startrow, nbrows):
    '''return a cell represented with a string (column) and an integer
       (row) whose index is the given one provided that it belongs to
       a region with nbrows in total which starts at startrow

    '''

    # apply here the typical formula
    return get_columnname (int (index / nbrows)) + str (startrow + (index % nbrows))

    
# classes
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# DBRange
#
# Definition of a simple range of cells which provides an iterator
# -----------------------------------------------------------------------------
class DBRange:
    """
    Definition of a single range of cells which provides an iterator
    """

    def __init__ (self, interval):

        '''defines a consecutive range of cells as an interval [start,
           end]. Both the start and end are represented with a string
           and a number. The string represents the column, whereas the
           number represents the row

        '''

        # copy the attributes
        self._start = interval [0]
        self._end   = interval [1]

        # get the starting/ending column/row of the interval with a
        # regular expression that creates groups for each part
        self._startcolumn, self._startrow = get_columnrow (self._start)
        self._endcolumn  , self._endrow   = get_columnrow (self._end)

        # make sure that start is less or equal than end so that all
        # the subsequent operations get much simpler
        if self._startrow < self._endrow:

            # Case 1: start is NW end
            if self._startcolumn < self._endcolumn:

                # Trivial case - This is the required representation
                pass

            # Case 2: start is NE end
            else:

                self._start = self._endcolumn   + str (self._startrow)
                self._end   = self._startcolumn + str (self._endrow)
            
        else:

            # Case 3: start is SW end
            if self._startcolumn < self._endcolumn:

                self._start = self._startcolumn + str (self._endrow)
                self._end   = self._endcolumn   + str (self._startrow)

            # Case 4: start is SE end
            else:

                self._start, self._end = self._end, self._start

        # now, start and end properly represent the upper left corner
        # and the lower right corner of the region
        self._startcolumn, self._startrow = get_columnrow (self._start)
        self._endcolumn  , self._endrow   = get_columnrow (self._end)
        
        # in preparation for the iterator just locate the first and
        # last cells of this region
        self._current = get_index (self._start, self._startrow,
                                   1 + self._endrow - self._startrow)
        self._enditer = get_index (self._end, self._startrow,
                                   1 + self._endrow - self._startrow)
        

    def __str__ (self):
        '''provides a human readable representation of the contents of this intance'''

        return "{0}:{1}".format (self._start, self._end)
        
    def __iter__ (self):
        '''defines the simplest case for iterators'''
        
        return self

    def __next__ (self):
        '''returns the next cell with the format <string><number> where string
           represents the column and number stands for the row

        '''

        # if we did not reach the limit
        if self._current <= self._enditer:

            # we will return THIS location, so we increment first
            self._current += 1

            # and decrement prior to execute the return statement
            return get_cellname (self._current-1, self._startrow, 1 + self._endrow - self._startrow)
        else:
            
            # restart the iterator for subsequent invocations of it
            self._current = get_index (self._start, self._startrow,
                                       1 + self._endrow - self._startrow)
            self._enditer = get_index (self._end, self._startrow,
                                       1 + self._endrow - self._startrow)

            # and stop the current iteration
            raise StopIteration ()

    def get_start (self):
        '''returns the start of the interval'''

        return self._start

    def get_end (self):
        '''returns the end of the interval'''

        return self._end


# -----------------------------------------------------------------------------
# DBRanges
#
# Definition of a collection of ranges of cells which provides an iterator
# -----------------------------------------------------------------------------
class DBRanges:
    """
    Definition of a collection of ranges of cells which provides an iterator
    """

    def __init__ (self, intervals):
        '''defines a list of intervals, each of the form [start, end]. All intervals
           should be instances of DBRange

        '''

        # copy the given intervals
        self._intervals = intervals
        
        # initialize the information used by the iterator
        self._ith = 0                           # _ith stores the current interval
        
    def __str__ (self):
        '''provides a human readable representation of the contents of this intance'''

        output = str ()
        for interval in self._intervals:
            output += "{0}; ".format (interval)
        
        return output

    def __add__ (self, other):
        '''extends this range of intervals, with another range of intervals'''

        self._intervals += other._intervals
        return self
    
    def __iter__ (self):
        '''defines the simplest case for iterators'''
        
        return self

    def __next__ (self):
        '''returns the next cell with the format <string><number> where string
           represents the column and number stands for the row

        '''

        try:

            # return the next element in the current interval if any is available
            return next (self._intervals [self._ith])
        
        except StopIteration:

            # start iterating over the next interval unless there are no more
            # intervals
            self._ith += 1
            if self._ith < len (self._intervals):

                # then point to the next interval and return the first item
                return next (self)

            else:
                
                # if there are no more intervals then stop the iteration, but
                # first restart the counter
                self._ith = 0
                raise StopIteration


    def get (self, position=-1):
        '''if no position is given, it returns the list of intervals of this
           instance. In case a non-negative value is provided as a position,
           then it returns the interval in that position

        '''

        if position < 0:
            return self._intervals
        return self._intervals [position]


# -----------------------------------------------------------------------------
# DBColumn
#
# Provides a definition of columns as they are stored in the database
# -----------------------------------------------------------------------------
class DBColumn:
    """
    Provides a definition of columns as they are stored in the database
    """

    def __init__ (self, name, ranges, ctype, action):
        '''defines a column with the given which should be populated with information
           from the cells in the specified ranges. All data read should be
           automatically casted into the given ctype. In case a cell contains no
           data, the specified action should be raised

        '''

        # copy the attributes given to the constructor
        self._name, self._ranges, self._type, self._action = (name, ranges, ctype, action)

        # and also intialize the container which should store the data retrieved
        # from the spreadsheet
        self._data = list ()

    def __str__ (self):
        '''provides a human-readable description of the contents of this database'''

        output = str ()                         # initialize the output string
        return "\t Name  : {0}\n\t Range : {1}\n\t Type  : {2}\n\t Action: {3}".format (self._name, self._ranges, self._type, self._action)

        
    def get_name (self):
        '''returns the name of this column'''

        return self._name

    def get_ranges (self):
        '''returns the ranges of this column'''

        return self._ranges

    def get_type (self):
        '''returns the type of this column'''

        return self._type

    def get_action (self):
        '''returns the action of this column'''

        return self._action

    def extend (self, length):
        '''replicates the length of this column only in case it consists of just one
        item to have as many as 'length'. In case the column has a distance
        which is larger than 1 and different than 'length' an error is raised

        Of course, this method should be invoked after looking up the
        spreadsheet

        '''

        # in case data consists of just one item
        if len (self._data) == 1:

            # then replicate its only item to have precisely length items
            self._data *= length

        elif len (self._data) != length:

            print (" Fatal Error in DBColumn::extend. It is not possible to extend column '{0}' which contains {1} items to hold {2} items".format (self._name, len (self._data), length))
            sys.exit (0)

        # and return the new container
        return self._data
        
    
    def lookup (self, spsname, sheetname=None):
        '''returns the contents of this column with data from the spreadsheet
           spsname. If a sheetname is given, then data is retrieved from the
           specified one

        '''

        # access the specified spreadsheet
        if not sheetname:
            sheet = pyexcel.get_sheet (file_name = spsname)
            sheetname = sheet.name                      # and copy the first sheet's name
        else:
            sheet = pyexcel.get_sheet (file_name = spsname, sheet_name=sheetname)

        # for all cells in all regions of this column
        for cell in self._ranges:

            # access the data
            data = sheet [cell]
            # print (" {0} [{1}]: {2}".format (spsname, cell, data))

            # in case there is no data in this cell
            if data == '':

                # apply the action specified in this instance
                if self._action == 'Error':              # in case of error
                    print (" Error - No data was found in cell '{0}' in database '{1}::{2}'".format (cell, spsname, sheetname))
                    sys.exit (0)

                elif self._action == 'Warning':          # in case of warning
                    print (" Warning - No data was found in cell '{0}' in database '{1}::{2}'".format (cell, spsname, sheetname))

                elif self._action != 'None':            # if it is neither an error, warning
                    data = self._action                 # or none, then it is a default value

            # now, cast data as specified in this instance
            if self._type == 'integer':
                data = int (data)
            elif self._type == 'real':
                data = float (data)
            elif self._type == 'text':
                data = str (data)

            # and add this data to the result
            self._data.append(data)

        # and return the result
        return self._data
    
        
# -----------------------------------------------------------------------------
# DBTable
#
# Provides the definition of a database table
# -----------------------------------------------------------------------------
class DBTable:
    """
    Provides the definition of a database table
    """

    def __init__ (self, name, columns):
        '''initializes a database table with the given name and information from all the
        given columns, which shall be instances of DBColumn

        '''

        self._name, self._columns = name, columns

    def __str__ (self):
        '''provides a human-readable description of the contents of this database'''

        output = str ()                         # initialize the output string
        output += " Name: {0}\n\n".format (self._name)
        for column in self._columns:
            output += "{0}\n\n".format (column)

        return output                           # return the output string
        
    def get (self, position=-1):
        '''if no position is given, it returns the list of columns of this instance. In
           case a non-negative value is provided as a position, then it returns
           the column in that position

        '''

        if position < 0:
            return self._columns
        return self._columns [position]

    def get_name (self):
        '''returns the name of this table'''

        return self._name
    
    def lookup (self, spsname, sheetname=None):
        '''looks up the given spreadsheet. If a sheetname is given, then it access that
           specified sheet; otherwisses, it uses the first one.

        '''

        # --- initialization
        maxlen = 0                      # length of the longest column
        
        # iterate over all columns to look up the spreadsheet
        for column in self._columns:

            # look up this specific table
            column.lookup (spsname, sheetname)
            maxlen = max (maxlen, len (column._data))

        # now, make sure that all columns have the same length
        for column in self._columns:

            column.extend (maxlen)

        # all columns are now the same length. Create a list of tuples, where
        # each tuple is a row in this database, i.e., a value from each column in
        # the same position
        data = list ()
        for irow in range (maxlen):                     # for all rows
            row = tuple ()                              # start with an empty tuple
            for column in self._columns:
                row += (column._data[irow],)            # add this value
            data.append (row)                           # and add this tuple

        # and return all data retrieved from the spreadsheet in the form of a
        # list of tuples, ready to be inserted into the database
        return data

    def create (self, cursor):
        '''creates a sqlite3 database table with the schema of its columns with the
           given name using the given sqlite3 cursor'''

        cmdline = 'CREATE TABLE ' + self._name + ' ('
        for column in self._columns[:-1]:               # for all columns but the last one
            cmdline += column.get_name () + ' '         # compose the name of the column
            cmdline += column.get_type () + ', '        # its type and a comma

        # do the same with the last one but with a closing parenthesis instead
        cmdline += self._columns[-1].get_name () + ' '
        cmdline += self._columns[-1].get_type () + ')'

        # and now, create the table
        cursor.execute (cmdline)

    def insert (self, cursor, spsname, sheetname=None):
        '''insert the data of this table in a sqlite3 database through the given sqlite3
           cursor. Data is retrieved from the given spreadsheet. If a sheetname
           is given, then it access that specified sheet; otherwisses, it uses
           the first one

        '''

        # create first the specification line to insert data into the sqlite3
        # database
        specline = "?, " * (len (self._columns) - 1)
        cmdline = "INSERT INTO %s VALUES (%s)" % (self._name, specline + '?')

        # retrieve now data from the spreadsheet (and/or the given sheetname)
        data = self.lookup (spsname, sheetname)

        # and insert data
        cursor.executemany (cmdline, data)

        
# -----------------------------------------------------------------------------
# DBDatabase
#
# Provides the definition of a database as a collection of tables
# -----------------------------------------------------------------------------
class DBDatabase:
    """
    Provides the definition of a database as a collection of tables
    """

    def __init__ (self, tables):
        '''initializes a database with the given tables which shall be instances of
           DBTable

        '''

        self._tables = tables
        self._current = 0               # used to iterate over tables

    def get (self, position=-1):
        '''if no position is given, it returns the list of tables of this instance. In
           case a non-negative value is provided as a position, then it returns
           the table in that position

        '''

        if position < 0:
            return self._tables
        return self._tables [position]

    def __add__ (self, other):
        '''extends this database with the tables found in another database'''

        self._tables += other._tables
        return self
    
    def __iter__ (self):
        '''defines the simplest case for iterators'''
        
        return self

    def __next__ (self):
        '''returns the next table in the definition of this database

        '''

        # if we did not reach the limit
        if self._current < len (self._tables):

            # and return the table in the current position (after incrementing)
            next = self._tables [self._current]
        
            self._current += 1                  # increment the counter
            return next                         # and return this one

        else:
            
            # restart the iterator for subsequent invocations of it
            self._current = 0

            # and stop the current iteration
            raise StopIteration ()

    def __str__ (self):
        '''provides a human-readable description of the contents of this database'''

        output = str ()                         # initialize the output string
        for table in self._tables:
            output += "{0}".format (table)  # format each table

        return output                           # and return the string

    def create (self, dbname):
        '''creates a sqlite3 database named 'databasename' with the schema of all tables
           in this instance

        '''

        # create a connection to the database
        self._dbname = dbname                   # store the name of the database
        self._conn = sqlite3.connect (dbname)   # connect to this database
        self._cursor = self._conn.cursor ()     # and get a cursor

        # create all tables in this database
        for table in self._tables:              # for all tables
            table.create (self._cursor)         # create it using this sqlite3 cursor

        # close the database
        self._conn.commit ()                    # commit all changes
        self._conn.close ()                     # close the database
            
    def insert (self, dbname, spsname, sheetname=None):
        '''inserts data from the given spreadsheet into the sqlite3 database named
           'databasename' according to the schema of all tables in this
           instance. If a sheetname is given, then it access that specified
           sheet; otherwisses, it uses the first one

        '''

        # create a connection to the database
        self._dbname = dbname                   # store the name of the database
        self._conn = sqlite3.connect (dbname)   # connect to this database
        self._cursor = self._conn.cursor ()     # and get a cursor

        # create all tables in this database
        for table in self._tables:              # for all tables

            # insert data into this table
            table.insert (self._cursor, spsname, sheetname) 

        # close the database
        self._conn.commit ()                    # commit all changes
        self._conn.close ()                     # close the database
            
    
# Local Variables:
# mode:python
# fill-column:80
# End:
