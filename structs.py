#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# structs.py
# Description: Basic structures used both by databases and spreadsheets
# -----------------------------------------------------------------------------
#
# Started on  <Thu Jul 19 07:29:38 2018 >
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
Basic structures used both by databases and spreadsheets
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.0'


# imports
# -----------------------------------------------------------------------------
import math                             # pow
import re                               # match


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

    
# -----------------------------------------------------------------------------
# add_rows
#
# returns a new cell which is the given number of rows away from
# it. If value is positive, it returns a cell below; otherwise, it
# returns a cell above
# -----------------------------------------------------------------------------
def add_rows (cellname, value):
    '''returns a new cell which is the given number of rows away from
       it. If value is positive, it returns a cell below; otherwise,
       it returns a cell above

    '''
    
    # get the current column and row of the specified cell
    (column, row) = get_columnrow (cellname)

    # verify you are not below the first row
    if row + value < 1:
        raise ValueError (" add_rows ({0}, {1}) goes above the first row".format (cellname, value))
    
    # return the name of a cell which is a given number of rows below
    # the current one
    return column + str (row + value)
    
# -----------------------------------------------------------------------------
# add_columns
#
# returns a new cell which is the given number of columns away from
# it. If value is positive, it returns a cell to its right; otherwise,
# it returns a cell to the left
# -----------------------------------------------------------------------------
def add_columns (cellname, value):
    '''returns a new cell which is the given number of columns away from
       it. If value is positive, it returns a cell to its right;
       otherwise, it returns a cell to the left

    '''

    # get the current column and row of the specified cell
    (column, row) = get_columnrow (cellname)

    # verify you are not below the first column
    if get_columnindex (column) + value < 0:
        raise ValueError (" add_columns ({0}, {1}) goes beyond the left margin".format (cellname, value))
    
    # return the name of a cell which is a given number of columns below
    # the current one
    return get_columnname (get_columnindex (column) + value) + str (row)
    
# -----------------------------------------------------------------------------
# Range
#
# Definition of a simple range of cells which provides an iterator
# -----------------------------------------------------------------------------
class Range:
    """
    Definition of a single range of cells which provides an iterator
    """

    def __init__ (self, interval):

        '''defines a consecutive range of cells as an interval [start,
           end]. Both the start and end are represented with a string
           and a number. The string represents the column, whereas the
           number represents the row. In spite of the start and end,
           data is privately normalized so that the start represents
           the upper left corner and the end represents the lower
           right corner of the range.

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

    def __len__ (self):
        '''returns the number of cells in this range'''

        return 1 + \
            get_index (self._end, self._startrow, 1 + self._endrow - self._startrow) - \
            get_index (self._start, self._startrow, 1 + self._endrow - self._startrow)
        
    def get_start (self):
        '''returns the start of the interval'''

        return self._start

    def get_end (self):
        '''returns the end of the interval'''

        return self._end

    def add_rows (self, value):
        '''returns a new range which is the given number of rows away from
           it. If value is positive, it returns a cell below;
           otherwise, it returns a cell above

        '''

        return Range ([add_rows (self._start, value), add_rows (self._end, value)])

    def add_columns (self, value):
        '''returns a new range which is the given number of columns away from
           it. If value is positive, it returns a cell to its right;
           otherwise, it returns a cell to the left

        '''

        return Range ([add_columns (self._start, value), add_columns (self._end, value)])

    def number_of_rows (self):
        '''return the number of rows in this range'''

        # get the row of the top left corner of this range, and also
        # the and row of the bottom right corner
        rowstart = get_columnrow (self._start)[1]
        rowend = get_columnrow (self._end)[1]

        # and return the number of rows
        return 1 + rowend - rowstart

    def number_of_columns (self):
        '''return the number of columns in this range'''

        # get the column of the top left corner of this range, and
        # also the column of the bottom right corner
        columnstart = get_columnrow (self._start)[0]
        columnend = get_columnrow (self._end)[0]

        # and return the number of columns
        return 1 + get_columnindex (columnend) - get_columnindex (columnstart)

        

# Local Variables:
# mode:python
# fill-column:80
# End:
