#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dbstructs.py
# Description: Definition of all classes required to represent the
# information parsed from a db file
# -----------------------------------------------------------------------------
#
# Started on  <Tue Jul 24 15:18:45 2018 >
# -----------------------------------------------------------------------------
#
# Carlos Linares Lopez
# Login   <carlos.linares@uc3m.es>
#

"""Definition of all classes required to represent the information
parsed from a db file

"""


# imports
# -----------------------------------------------------------------------------
from collections import defaultdict

import os                               # access
import re
import sqlite3
import sys                              # exit

import pyexcel

from . import structs
from . import utils

# globals
# -----------------------------------------------------------------------------
LOGGER = utils.LOGGER

# -- errors
ERROR = "Error - {0}"
ERROR_INVALID_CELL_SPECIFICATION = "The cell '{0}' is not a legal expression, neither implicit nor explicitly"
ERROR_INVALID_EXPLICIT_CELL_SPECIFICATION = "The cell '{0}' is not a legal explicit cell"
ERROR_INVALID_IMPLICIT_CELL_SPECIFICATION = "The cell '{0}' is not a legal implicit cell"
ERROR_COLUMN_INDEX = "Column {0} out of index while looking for cell '{1}'"
ERROR_ROW_INDEX = "Row {0} out of index while looking for cell '{1}'"
ERROR_UNKNOWN_TYPE = "The default value '{0}' defined for column '{1}' is an instance of an unknown type '{2}'"
ERROR_CAST_COLUMN = "It was not possible to cast the default value '{0}' defined for column '{1}' to the type '{2}'"
ERROR_CAST_DBCOLUMN = "It was not possible to cast the value '{0}' in '{1}::{2}' to the type {3}"
ERROR_CAST_CELL = "It was not possible to cast the value '{0}' found in cell {1} in '{2}::{3}' to the type {4}"
ERROR_EXTENT = "It is not possible to extend column '{0}' which contains {1} items to hold {2} items"
ERROR_NO_DATA = "No data was found in cell '{0}' in '{1}::{2}'"
ERROR_CONTENT_UNKNOWN_TYPE = "Unknown type for content {0}"
ERROR_KEY_NOT_FOUND_IN_CONTEXT = "Modifier '{0}' not found in context"
ERROR_DIFF_BLOCKS = """The block
{0}

is not equal to the block

{1}"""
ERROR_BLOCK_UNSPECIFIED_TYPE = """
The block

{0} contains columns with unspecified types"""
ERROR_TABLE_EXISTS = "Table '{0}' already exists"
ERROR_NO_SPREADSHEET = "No spreadsheet has been given"
ERROR_FILE_EXISTS = "The file '{0}' already exists!"

# -- warnings
WARNING = "{0}"
WARNING_DUPLICATED_ROW = "Duplicated row: {0}"
WARNING_NOT_EQUAL = "{0} != {1} rows generated"
WARNING_EQUAL = "{0} = {1} rows generated"
WARNING_LESS = "{0} < {1} rows generated"
WARNING_GREATER = "{0} > {1} rows generated"

# -- info
INFO_LOOKING_UP_COLUMN = "\t > Looking up column {0}"

# -- literals
STR_DBCOLUMN = "\t Name    : {0}{1}\n\t Contents: {2}\n\t Type    : {3}\n\t Action  : {4}"

# classes
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# DBAction
#
# Definition of actions
# -----------------------------------------------------------------------------
class DBAction:
    """
    Definition of actions
    """

    def __init__(self, action:str, default=None):

        '''an action consists of either ignoring (None), warning or issuing an error,
           given as a string. Additionally, in the first two cases, default
           values shall be specified

        '''

        # copy the attributes
        self._action, self._default = action, default


    def __str__(self):
        '''provides a human readable representation of the contents of this intance'''

        # in case of an error, no default is needed
        if self._action == "Error":
            return self._action

        # otherwise return both the action and the default value
        return "{0} with default value: {1}".format(self._action, self._default)


    def get_action(self):
        '''return the action specified in this instance'''

        return self._action


    def get_default(self):
        '''return the default value of this action'''

        return self._default


    def handle_action(self, name:str, ctype:str, message=''):
        '''applies this action to a column named "name" which is defined to store values
           of the specified type. It returns the data to be used with the
           correct type

        '''

        # apply the action specified in this instance
        if self._action == 'Error':                             # in case of error

            # raise an error
            LOGGER.error(message)
            raise RuntimeError(message)

        if self._action == 'Warning':                           # in case of warning

            # show a warning message and use the default value defined for this
            # column
            LOGGER.warning(WARNING.format(message))
            data = self._default

        # if it is neither an error nor a warning, silently copy the default
        # value defined in the action of this column
        data = self._default

        # if the default value is None then just return that, otherwise cast the
        # default value to the specified type
        if self._default is not None:

            # before returning ensure that the default value can be casted into the
            # type specified for this column
            try:

                # now, cast the default value as specified in this instance
                if ctype == 'integer':
                    data = int(data)
                elif ctype == 'real':
                    data = float(data)
                elif ctype in ['text', 'datetime', 'date']:
                    data = str(data)
                else:
                    LOGGER.error(ERROR_UNKNOWN_TYPE.format(data, name, ctype))
                    raise TypeError(ERROR_UNKNOWN_TYPE.format(data, name, ctype))

            except:

                # if it was not possible then raise an error
                LOGGER.error(ERROR_CAST_COLUMN.format(data, name, ctype))
                raise TypeError(ERROR_CAST_COLUMN.format(data, name, ctype))

        # finally, return the default value as computed here
        return data


# -----------------------------------------------------------------------------
# DBExplicit
#
# Definition of data explicitly given.
# -----------------------------------------------------------------------------
class DBExplicit:
    """
    Definition of data explicitly given
    """

    def __init__(self, data):
        '''data (of any of the basic types: date, datetime, integers, floating-point
           numbers and strings is defined explicitly just by providing it.

           Note that the type of data is not verified for consistency at the
           time of its creation, but later when it is about to be used

        '''

        # copy the given data as a list
        self._data = data

    def __str__(self):
        "provide a human-readable representation of the contents of this instance"

        return " Explicit data ({0})".format(self._data)

    def get_data(self):
        """return the data given in this explicit definition"""

        return self._data


# -----------------------------------------------------------------------------
# DBCellReference
#
# Definition of a cell given either explicitly or implicitly and an optional
# offset
# -----------------------------------------------------------------------------
class DBCellReference:
    """Definition of a cell given either explicitly or implicitly and an optional
    offset

    """

    def __init__(self, descriptor:str, coloffset=0, rowoffset=0):
        """Cells can be given either explicitly or implicitly in the descriptor given as
           a string with the format <alpha><num>:

              * Explicitly: cells are identified by their coords, e.g., B24

              * Implicitly: cells can be identified by various means:

                + By the *global* length. Either the row, the column or both can
                  be automatically determined such that the length of the
                  resulting range is equal to the length of the context of the
                  block where it is processed. This definition requires another
                  cell to be used in the comparison, e.g., $B* should be equal
                  to $B6 if it is given with either $B4 or $B8 and length is 3

                + By the range. Either the first/last row or the column (but not
                  both) can be directly retrieved from the spreadsheet. '.'
                  refers to the first row/column if it appears in the first cell
                  of the range as in $A.:$A20, and it is the last element when
                  it appears in the second cell of the range as in $B10:$.10.
                  Note that the first/last row/column refers to the first
                  non-empty cell in the entire spreadsheet, i.e, to one of the
                  coordinates of the bounding rectangle where data is shown in
                  the spreadsheet.

                  Obviously, cell references fully ignore whether a cell is
                  first or last.

                + By their content. Either the row or the column (but not both)
                  is characterized by its content between square brackets, e.g.,
                  $B[100] is the cell in the first row in column B whose content
                  is precisely equal to 100. It is also possible to give empty
                  cells such as in $[]3 which is the cell in the first column of
                  the third row whose content is empty

           Additionally, cells can be referenced with an offset (either positive
           or negative) of columns and rows

        """

        # copy the attributes
        self._descriptor, self._coloffset, self._rowoffset = descriptor, coloffset, rowoffset

        # by default the location of this cell is unknown until the execution
        # method is invoked
        self._cell = None


    def get_descriptor(self):
        """ returns the descriptor of this cell"""

        return self._descriptor


    def get_coloffset(self):
        """ returns the column offset of this cell"""

        return self._coloffset


    def get_rowoffset(self):
        """ returns the row offset of this cell"""

        return self._rowoffset

    def get_cell(self):
        """ returns the cell referenced by this instance"""

        return self._cell

    def __str__(self):
        '''provides a human readable representation of the contents of this intance'''

        if self._coloffset or self._rowoffset:
            output = self._descriptor + \
                " + (" + str(self._coloffset) + ", " + str(self._rowoffset) + ")"
        else:
            output = self._descriptor

        # if this cell is already known
        if self._cell:
            output += " [{0}]".format(self._cell)

        # otherwise return a textual interpretation of the contents of this instance
        return output


    def _do_range(self, context, base: str):
        """substitutes the '.' symbol in the description of this cell using the range
           values given in the context. This is a destructive function which
           overwrites the contents of self._descriptor

           If no base is given, then the *first* cell is returned which is
           either the min_column or the min_row stored in the context. However,
           if a base is given, then the first cell *after* it has to be returned
           and the only possibility here is to return either max_column or
           max_row

           Note that the dot can be combined with itself in a cell reference as
           in $.., which is then substituted with the lower-right corner of the
           spreadsheet

           This operator enables reusability of the same db description files
           even if the contents of the spreadsheet change

        """

        # does the dot appear in the column? Note that we just simply verify
        # that the first character is the dot.
        if self._descriptor[0] == '.':

            # In the following, one is substracted from the value of the column
            # retrieved from the context, because structs.get_getcolumnname
            # numbers columns from zero so that 'A' is 0 but pyexcel would give
            # this column the value 1
            if not base:
                self._descriptor = structs.get_columnname(context["min_column"][0]-1) + \
                    self._descriptor[1:]
            else:
                self._descriptor = structs.get_columnname(context["max_column"][0]-1) + \
                    self._descriptor[1:]

        # does the dot appear in the row? Note that we just simply verify that
        # the last character is the dot
        if self._descriptor[-1] == '.':

            if not base:
                self._descriptor = self._descriptor[:-1] + str(context["min_row"][0])
            else:
                self._descriptor = self._descriptor[:-1] + str(context["max_row"][0])


    def _do_length(self, ref, context):
        """substitutes the '*' symbol in the description of this cell using the
           reference description such that both cells create a range equal to
           the length reported in the context.

           The following descriptions assume that the descriptor of this cell
           contains '*' whereas the reference cell does not. Indeed, '*' can not
           be present in both the descriptor of this cell and the reference one,
           i.e., the reference one should be fully qualified and therefore there
           is no point in dissambiguating it

           1. Determine where the '*' is given in the descriptor

           2. The value of '*' is obtained from an offset that can be either
              added or substracted. The offset is equal to the length reported
              in the context divided by the absolute value of the difference
              between the other coordinates (plus one, to include both)

           3. If the 'non-*' coordinate of the descriptor is less than the
              'non-*' coordinate of the reference cell, then offset has to be
              substracted to the other coordinate

        """

    def _traverse_cells(self, sheet:pyexcel.Sheet, base=None):
        """compute the exact location of this cell in a two-step process:

           1. If the descriptor defines a cell in explictit form return it
              immediately

           2. If the descriptor defines a cell in implicit form then traverse
              the given sheet in the right direction to determine its location

           Note that:

           1. Step 2 requires access to the spreadsheet as given in sheet.

           2. The only implicit definition of cell references accepted by this
              function is "by content" with the operator '[]', i.e., if this
              cell reference contained other operators such as '.' or '*' these
              should have been resolved before invoking this function.

           In addition a base can be given for computing the exact location of
           cells defined implicitly. If a base is given, the location to look
           for should be *after* the given base

           This method entirely ignores the offset of this instance

        """

        # First things first, check whether the cell has been given explicitly
        # in the form <column><row>
        if re.match(r'[a-zA-Z]+\d+', self._descriptor):

            # in this case, the given cell is returned immediately in spite of
            # the base
            return self._descriptor

        # Now, process the cell implicitly. The following regexp returns four
        # different groups (column0, row0, column1, row1), if the cell has been
        # given as <column0>[row0] or [column1]<row1>
        regexp0 = r'(?P<column0>[a-zA-Z]+)\[(?P<row0>.*)\]'
        regexp1 = r'\[(?P<column1>.*)\](?P<row1>\d+)'
        match = re.match(regexp0 + '|' + regexp1, self._descriptor)
        if not match:
            LOGGER.error(ERROR_INVALID_CELL_SPECIFICATION.format(self._descriptor))
            raise ValueError(ERROR_INVALID_CELL_SPECIFICATION.format(self._descriptor))

        # process the base which should be given explicitly in the form
        # <column><row> if any was given. These values of column and cell are
        # the initial values for the column and the cell when looking for the
        # specific cell matching its contents with those specified in the cell
        if base:
            column, row = structs.get_columnrow(base)
        else:
            column, row = 'A', 1

        # if the cell was given in the format <colum>[content]
        if match.groups()[0] is not None and match.groups()[1] is not None:

            # then the increment between adjacent cells should proceed by rows
            column, delta, content = match.groups()[0], (0, 1), match.groups()[1]

        elif match.groups()[2] is not None and match.groups()[3] is not None:

            # if otherwise, this cell was given in the format [content]<row>
            # then the increment should proceed by columns, and the content was
            # given first
            row, delta, content = match.groups()[3], (1, 0), match.groups()[2]

        else:

            # something went deeply wrong here!
            LOGGER.error(ERROR_INVALID_IMPLICIT_CELL_SPECIFICATION.format(self._descriptor))
            raise ValueError(ERROR_INVALID_IMPLICIT_CELL_SPECIFICATION.format(self._descriptor))

        # verify now that this column and row are within the range of the
        # spreadsheet. If not immediately raise an error
        current = column + str(row)
        if structs.get_columnindex(column) >= sheet.column_range().stop:
            LOGGER.error(ERROR_COLUMN_INDEX.format(column, self._descriptor))
            raise IndexError(ERROR_COLUMN_INDEX.format(column, self._descriptor))
        if int(row) > sheet.row_range().stop:
            LOGGER.error(ERROR_ROW_INDEX.format(row, self._descriptor))
            raise IndexError(ERROR_ROW_INDEX.format(row, self._descriptor))

        # so just locate at the given row and column and proceed applying the
        # given delta until a cell is found with the specified contents. current
        # is the cell examined at each iteration
        while str(sheet[current]) != str(content):

            # move to the next cell
            current = structs.add_columns(structs.add_rows(current, delta[1]), delta[0])
            (column, row) = structs.get_columnrow(current)
            if structs.get_columnindex(column) >= sheet.column_range().stop:
                LOGGER.error(ERROR_COLUMN_INDEX.format(column, self._descriptor))
                raise IndexError(ERROR_COLUMN_INDEX.format(column, self._descriptor))
            if row > sheet.row_range().stop:
                LOGGER.error(ERROR_ROW_INDEX.format(row, self._descriptor))
                raise IndexError(ERROR_ROW_INDEX.format(row, self._descriptor))

        # and return the cell that matches the contents given in the cell beyond
        # the base, if any was given
        return current


    def execute(self, context, sheet, base=None):
        """determine the exact location this instance refers to in a two-step
           process:

           1. Translate the explicit/implicit definition of this cell to a
              specific cell

           2. Apply the offset of this instance to return the final location

           Not that the first point might require access to the context and/or
           the spreadsheet in case the cell is defined implicitly. In addition,
           when looking for the contents of a specific cell a base can be given
           so that the resulting cell has to be *after* it

        """

        # first, update the descriptor of this instance if the dot operator '.'
        # was used. The result of _do_range is an explicit representation of
        # this cell which is directly returned by _traverse_cells
        self._do_range(context, base)

        # Now, in case the [] operator has been used then use _traverse_cells to
        # obtain the right location of this cell. Otherwise, an explicit
        # representation of this cell should be available which is directly
        # returned by _traverse_cells. In passing, apply the offset of this
        # instance to the resulting cell
        self._cell = structs.add_rows(structs.add_columns(self._traverse_cells(sheet, base),
                                                          self._coloffset),
                                      self._rowoffset)
        return self._cell


# -----------------------------------------------------------------------------
# DBRange
#
# Definition of a range of cells given as instances of DBCellReference
#
# The second cell has to be *after* the first one. However, if the user gave an
# offset this rule might be easily broken
# -----------------------------------------------------------------------------
class DBRange:
    """Definition of a range of cells given as instances of DBCellReference

       The second cell has to be *after* the first one. However, if the user
       gave an offset this rule might be easily broken

    """

    def __init__(self, start: DBCellReference, end: DBCellReference):
        '''defines a range of cells which can be given either impliclty or explicilty.
          'start' and 'end' should be given as instances of DBCellReference

        '''

        # copy the given attributes
        self._start, self._end = start, end

        # and initialize the instantiated range to none
        self._range = None


    def __str__(self):
        """Provides a human readable representation of the contents of this instance"""

        if self._range:
            return "{0}:{1} = {2}".format(self._start, self._end, self._range)
        return "{0}:{1}".format(self._start, self._end)


    def get_range(self, context, sheet):
        """returns an instantiated range of cells, i.e., it computes the specific cells
           that result of *executing* (i.e., translating) the start and end of
           this range, either if they are given in implicit/explicit form and
           after adding the offset if any is given

           The context and sheet might be necessary in case any cell is given in
           implicit form.

        """

        # first, compute the exact locations of the start and end cells of this
        # range. The start cell is computed as the first cell satisfying the
        # definition of its own cell reference (i.e., if "B." is given then it
        # is the first column with data); whereas the end cell has to be
        # necessarily after the start cell, e.g. if "B[114]" is given and start
        # is B6, then it is the first cell in the first row of the second column
        # after the sixth column whose content equals 114
        start = self._start.execute(context, sheet)
        end = self._end.execute(context, sheet, start)

        # and return a range properly formed with these cells
        self._range = structs.Range([start, end])
        return self._range


# -----------------------------------------------------------------------------
# DBContents
#
# Definition of a collection of contents which can be either ranges of cells or
# contents explicitly given. This container provides an iterator
# -----------------------------------------------------------------------------
class DBContents:
    """Definition of a collection of contents which can be either ranges of cells
       or contents explicitly given. This container provides an iterator

    """

    def __init__(self, intervals: list):
        '''defines a list of contents, each one can be either a content explicitly
           given, or a range of cells

           Contents explicitly given should be instances of DBExplicit, whereas
           ranges should be given as instances of DBRange

        '''

        # copy the given intervals
        self._intervals = intervals

        # initialize the information used by the iterator
        self._ith = 0                           # _ith stores the current interval

    def __str__(self):
        '''provides a human readable representation of the contents of this intance'''

        output = str()
        for interval in self._intervals:
            output += "{0}".format(interval)

        return output

    def __add__(self, other: list):
        '''extends this range of intervals, with another range of intervals'''

        self._intervals += other._intervals
        return self

    def __iter__(self):
        '''defines the simplest case for iterators'''

        return self

    def __next__(self):
        '''returns the next item in this container, either a range of cells or a content
           explicitly given

        '''

        # if we did not reach the limit
        if self._ith < len(self._intervals):

            # return the item in the current position (after incrementing)
            item = self._intervals[self._ith]
            self._ith += 1
            return item

        # restart the iterator for subsequent invocations of it
        self._ith = 0

        # and stop the current iteration
        raise StopIteration()

    def get(self, position=-1):
        '''if no position is given, it returns the list of intervals of this
           instance. In case a non-negative value is provided as a position,
           then it returns the interval in that position

        '''

        if position < 0:
            return self._intervals
        return self._intervals[position]


# -----------------------------------------------------------------------------
# DBColumn
#
# Provides a definition of columns as they are stored in the database
# -----------------------------------------------------------------------------
class DBColumn:
    """
    Provides a definition of columns as they are stored in the database
    """

    def __init__(self, name, contents, ctype, action, *qualifiers):
        '''defines a column with the given name which should be populated with the
           specified contents. Contents can be either ranges of cells whose
           value has to be retrieved from the database or data explicitly given
           and should be given as instances of DBContents

           All data read should be automatically casted into the given ctype. In
           case a cell contains no data, the specified action should be raised.
           Actions should be one among:

           Error - raises an exception immediately stopping execution
           Warning - warns the user and resumes execution
           None - nothing is done

           If the action is either warning or none, a default value can be given
           to be inserted when nothing is found in the spreadsheet. Default
           values are automatically casted to the column types

           Additionally, any qualifiers can be given in the last parameter.
           Values accepted are listed below:

           INDEX - This column is an index
           KEY - This column is part of a PRIMARY KEY
           UNIQUE - This column is unique across insertions/updates

        '''

        # copy the attributes given to the constructor
        (self._name, self._contents, self._type, self._action, self._qualifiers) = \
            (name, contents, ctype, action, qualifiers)

        # and also intialize the container which should store the data retrieved
        # from the spreadsheet
        self._data = list()

    def __eq__(self, other):
        '''a column is equal to another if and only if they have the same name in spite
           of all the other attributes'''

        return self._name == other._name

    def __str__(self):
        '''provides a human-readable description of the contents of this column'''

        return STR_DBCOLUMN.format(self._name, '(*)' if self.is_key() else '',
                                   self._contents, self._type, self._action)

    def get_name(self):
        '''returns the name of this column'''

        return self._name

    def get_contents(self):
        '''returns the contents of this column'''

        return self._contents

    def get_type(self):
        '''returns the type of this column'''

        return self._type

    def get_action(self):
        '''returns the action of this column'''

        return self._action

    def is_index(self):
        '''returns whether this column is an index or not'''

        return "index" in self._qualifiers

    def is_key(self):
        '''returns whether this column is a key or not'''

        return "key" in self._qualifiers

    def is_unique(self):
        '''returns whether this column is subjected to a UNIQUE constraint'''

        return "unique" in self._qualifiers

    def get_data(self):
        '''return the data in this column'''

        return self._data

    def extend(self, length):
        '''replicates the length of this column only in case it consists of just one
        item to have as many as 'length'. In case the column currently has a
        cardinality larger than 1 and different than 'length' an error is raised

        Of course, this method should be invoked after looking up the
        spreadsheet

        '''

        # in case data consists of just one item
        if len(self._data) == 1:

            # then replicate its only item to have precisely length items
            self._data *= length

        elif len(self._data) != length:

            LOGGER.error(ERROR_EXTENT.format(self._name, len(self._data), length))
            sys.exit(0)

        # and return the new container
        return self._data


    def lookup(self, context, spsname: str, sheetname=None):
        '''returns the contents of this column. If it consists of data explicitly given,
           then it returns it right away after casting it to the appropriate
           type; if the contents of this column consist of ranges of cells, then
           it access the spreadsheet to retrieve them

           Columns accept ranges in various implicit formats. For
           dissambiguating them, the context of the block this column belongs to
           is mandatory. The context has to be given as an instance of DBContext

           In case the sheet has to be used, if a sheetname is given, then data
           is retrieved from the specified one

        '''

        # for all contents in this column
        for content in self._contents:

            # EXPLICIT DATA
            # ---------------------------------------------------------------------
            # if the contents of this data consist of data explicitly given then
            # just return it right away
            if isinstance(content, DBExplicit):

                try:

                    # now, cast data as specified in this instance
                    data = content.get_data()
                    if self._type == 'integer':
                        data = int(data)
                    elif self._type == 'real':
                        data = float(data)
                    elif self._type == 'text' or self._type == 'date':
                        data = str(data)

                except Exception:

                    # then apply the action specified in this column as well and
                    # retrieve the default value
                    data = self._action.handle_action(self._name, self._type,
                                                      ERROR_CAST_DBCOLUMN.format(data,
                                                                                 spsname,
                                                                                 sheetname,
                                                                                 self._type))

                # and add this data to the result
                self._data.append(data)

            # LIST OF REGIONS
            # ---------------------------------------------------------------------
            # for all cells in all regions of this column access the specified
            # spreadsheet
            elif isinstance(content, DBRange):

                # first, gain access to the spreadsheet
                if not sheetname:
                    sheet = pyexcel.get_sheet(file_name=spsname)
                    sheetname = sheet.name          # and copy the first sheet's name
                else:
                    sheet = pyexcel.get_sheet(file_name=spsname, sheet_name=sheetname)

                # now, for all cells in the range instantiated of this dbrange
                for cell in content.get_range(context, sheet):

                    # access the data
                    try:

                        # enclose this look up in a try-except block because there might
                        # be any errors, including "Index out of range"
                        data = sheet[cell]

                    except Exception:

                        # if an error is issued, then just simply consider there is no data
                        data = ''

                    # in case there is no data in this cell
                    if data == '':

                        # then apply the action specified in this column and retrieve
                        # the default value to use
                        data = self._action.handle_action(self._name, self._type,
                                                          ERROR_NO_DATA.format(cell,
                                                                               spsname,
                                                                               sheetname))

                    # if a value is found in this cell but ...
                    else:

                        # it is not possible to cast it to the type specified for this
                        # column
                        try:

                            # now, cast data as specified in this instance
                            if self._type == 'integer':
                                data = int(data)
                            elif self._type == 'real':
                                data = float(data)
                            elif self._type == 'text' or self._type == 'date':
                                data = str(data)

                        except Exception:

                            # then apply the action specified in this column as well and
                            # retrieve the default value
                            data = self._action.handle_action(self._name, self._type,
                                                              ERROR_CAST_CELL.format(data,
                                                                                     cell,
                                                                                     spsname,
                                                                                     sheetname,
                                                                                     self._type))

                    # and add this data to the result
                    self._data.append(data)

            else:
                LOGGER.error(ERROR_CONTENT_UNKNOWN_TYPE.format(content))
                raise TypeError(ERROR_CONTENT_UNKNOWN_TYPE.format(content))

        # and return the result
        return self._data


# -----------------------------------------------------------------------------
# DBModifier
#
# Provides the definition of a block modifier
# -----------------------------------------------------------------------------
class DBModifier:
    """
    Provides the definition of a block modifier
    """

    def __init__(self, name: str, *args):
        """Modifiers are distinguished with a name and qualified with a number of
           arguments

        """

        # copy the attributes
        self._name, self._args = name, args


    def __eq__(self, other: str):
        """returns whether this modifier has the name given in other"""

        return self._name == other


    def __str__(self):
        """provides a human-readable description of the contents of this instance"""

        output = "{0}".format(self._name)
        if self._args:
            output += ' ('
            for iarg in self._args[:-1]:
                output += "{0}, ".format(iarg)
            output += "{0})".format(self._args[-1])
        return output

    def get_name(self):
        """return the name of this instance"""

        return self._name


    def get_args(self):
        """return the arguments of this instance"""

        return self._args


# -----------------------------------------------------------------------------
# DBContext
#
# Contexts are defined as containers of block modifiers. Contexts contain
# variables that can be used in the description of blocks
# -----------------------------------------------------------------------------
class DBContext:
    """Contexts are defined as containers of block modifiers. Contexts contain
       variables that can be used in the description of blocks

    """

    def __init__(self, modifier: DBModifier):
        '''Initializes this context with the given modifier which shall be given as an
        instance of DBModifier

        '''

        # initialize the list ---note that it holds no default values
        # intentionally to avoid mistakes, so that only values defined in the
        # context can be used later
        self._modifiers = [modifier]

        # initialize the counter used in the iteration
        self._current = 0


    def __add__(self, right):
        """add the context given in right (as an instance of DBContext) to this context.
           It overwrites previous contents in case the variable already exists
           in this context

        """

        for imodifier in right:

            # if this modififer already exists, overwrite it by removing it the
            # value stored in this instance
            if imodifier.get_name() in self._modifiers:
                self._modifiers.remove(imodifier)

            # add the given modifier
            self._modifiers.append(imodifier)

        # and return this instance
        return self


    def __contains__(self, other):
        """return true if and only if there is a modifier in this context whose name
           matches other

           other can be given either as an instance of DBModifier or as a string
        """

        # otherwise directly compare them and return whether it has been found
        # or not
        return other in self._modifiers


    def __getitem__(self, key: str):
        """Called to implement evaluation of self[key]. If key does not exist, an
           exception is immediately raised"""

        if key not in self._modifiers:
            LOGGER.error(ERROR_KEY_NOT_FOUND_IN_CONTEXT.format(key))
            raise KeyError(ERROR_KEY_NOT_FOUND_IN_CONTEXT.format(key))
        return self._modifiers[self._modifiers.index(key)].get_args()


    def __setitem__(self, key: str, value):
        """Called to implement assignment to self[key]. If key exists it is
           overwritten"""

        if key in self._modifiers:
            self._modifiers[self._modifiers.index(key)] = DBModifier(key, value)
        else:
            self._modifiers.append(DBModifier(key, value))

        return self


    def __str__(self):
        """return a human readable version of the contents of this context"""

        output = ""
        for imodifier in self._modifiers:
            output += "{0}\n".format(imodifier)
        return output

    def __iter__(self):
        '''defines the simplest case for iterators'''

        return self

    def __next__(self):
        '''returns the next cell with the format <string><number> where string
           represents the column and number stands for the row

        '''

        # if we did not reach the limit
        if self._current < len(self._modifiers):

            # we will return this location, so we increment first
            imodifier = self._modifiers[self._current]
            self._current += 1

            # and decrement prior to execute the return statement
            return imodifier

        # restart the iterator for subsequent invocations of it
        self._current = 0

        # and stop the current iteration
        raise StopIteration()


# -----------------------------------------------------------------------------
# DBBlock
#
# Provides the definition of a table block. A block consists of a definition of
# different columns
# -----------------------------------------------------------------------------
class DBBlock:
    """
    Provides the definition of a table block. A block consists of a definition of
    different columns
    """

    def __init__(self, columns: list, context=None):
        '''initializes a block as a sequence of columns. Columns shall be given as a
           list of instances of DBColumn. Modifiers affect the behaviour of the
           table and should be given within a context as an instance of DBContext

           Valid modifiers are the following:

              * enforce_unique: discard duplicated rows without further ado

              * check_duplicates: verifies that all rows are diff. If not, a
                warning is shown but still all rows are inserted into the table

              * geq <NUMBER>: verifies that the number of rows generated is at
                least the given NUMBER

              * leq <NUMBER>: verifies that the number of rows generated is less
                or equal than the given NUMBER

              * eq <NUMBER>: verifies that the number of rows generated is
                strictly equal to the given NUMBER

              * neq <NUMBER>: verifies that the number of rows generated is
                strictly different than the given NUMBER

              * len <NUMBER>: provides the number of consecutive cells to read
                in those cases where a range is given as <START>: (i.e., without
                explicitly giving an <END>)

           In addition, a number of different qualiiers can be given on
           individual columns on any combination:

              * KEY: declares a column (or more) to be a KEY

              * INDEX: defines an index on a column (or more)

              * UNIQUE: sets up a SQL constraint UNIQUE on one column (or more)

        '''

        # copy the attributes
        self._columns, self._context = columns, context

        # in case no context was given, then create an empty one. To create an
        # empty context, an empty modifier is used
        if not self._context:
            self._context = DBContext("")

        # process all columns to get a list of all primary keys
        self._keys = []
        for icolumn in self._columns:
            if icolumn.is_key():
                self._keys.append(icolumn)

        # in addition, process all columns to get a list of all indexes
        self._indexes = []
        for icolumn in self._columns:
            if icolumn.is_index():
                self._indexes.append(icolumn)

        # also, process all columns to get a list of all that are subjected to a
        # UNIQUE constraint
        self._uniques = []
        for icolumn in self._columns:
            if icolumn.is_unique():
                self._uniques.append(icolumn)


    def get_columns(self):
        """return the columns of this block"""

        return self._columns

    def get_indexes(self):
        """return the indexes of this block"""

        return self._indexes

    def get_keys(self):
        """return the primary keys of this block"""

        return self._keys

    def get_context(self):
        """return the context of this block"""

        return self._context

    def get_uniques(self):
        """return all columns in this block subjected to the SQL UNIQUE constraint"""

        return self._uniques

    def get_nbkeys(self):
        """return the number of primary keys of this block"""

        return len(self._keys)

    def get_nbuniques(self):
        """return the number of SQL UNIQUE constraints defined in this block"""

        return len(self._uniques)

    def __eq__(self, other):
        '''one block is equal to another if and only if they have the same columns
           (i.e., with the same name) in precisely the same order'''

        return self._columns == other._columns

    def __ne__(self, other):
        '''return whether one block is not equal to another'''

        return not self.__eq__(other)

    def __str__(self):
        '''provides a human-readable description of the contents of this block'''

        output = str()                         # initialize the output string

        # first, show the context of this block, if any
        if self._context:
            output += "\t Context: \n"
            for imodifier in self._context:
                output += "\t\t {0}\n".format(imodifier)
            output += "\n"

        for column in self._columns:
            output += "{0}\n\n".format(column)

        return output                           # return the output string

    def lookup(self, spsname: str, sheetname=None):
        '''looks up the given spreadsheet and returns a list of tuples to insert in a
           sqlite3 database. If a sheetname is given, then it access that
           specified sheet; otherwisses, it uses the first one.

        '''

        def _get_min_row(sheet: pyexcel.Sheet):
            """return the first non empty row in the range of columns
               [1,sheet.column_range().stop]

            """

            # for all rows
            for irow in range(1, 1+sheet.row_range().stop):

                # for all columns
                for icolumn in range(0, sheet.column_range().stop):

                    # in case this is a non-empty cell immediately return the
                    # row index
                    if sheet[structs.get_columnname(icolumn) + str(irow)]:
                        return irow

        def _get_min_column(sheet: pyexcel.Sheet):
            """return the first non empty colum in the range of columns
               [1,sheet.column_range().stop]

            """

            # for all columns
            for icolumn in range(1, 1+sheet.column_range().stop):

                # for all rows
                for irow in range(1, 1+sheet.row_range().stop):

                    # in case this is a non-empty cell immediately return the
                    # row index
                    if sheet[structs.get_columnname(icolumn-1) + str(irow)]:
                        return icolumn


        # --- initialization
        maxlen = 0                      # length of the longest column

        # first, gain access to the spreadsheet
        if not sheetname:
            sheet = pyexcel.get_sheet(file_name=spsname)
            sheetname = sheet.name          # and copy the first sheet's name
        else:
            sheet = pyexcel.get_sheet(file_name=spsname, sheet_name=sheetname)

        # ensure that the context of this block contains all necessary
        # information for dissambiguating some implicit formats of ranges that
        # might be given in its columns
        if "min_column" not in self._context:
            self._context["min_column"] = _get_min_column(sheet)
        if "min_row" not in self._context:
            self._context["min_row"] = _get_min_row(sheet)
        if "max_column" not in self._context:
            self._context["max_column"] = sheet.column_range().stop
        if "max_row" not in self._context:
            self._context["max_row"] = sheet.row_range().stop

        # iterate over all columns to look up the spreadsheet
        for column in self._columns:

            LOGGER.info(INFO_LOOKING_UP_COLUMN.format(column.get_name()))

            # look up this specific table
            column.lookup(self._context, spsname, sheetname)
            maxlen = max(maxlen, len(column.get_data()))

        # now, make sure that all columns have the same length
        for column in self._columns:

            column.extend(maxlen)

        # in preparation to create rows (by aligning the data of all columns),
        # create a default dict that registers the number of occurrences of each
        # row. This dictionary is then used by modifiers
        # enforce_unique/check_duplicates. Also count the number of rows finally
        # generated
        nbrows = 0
        unique = defaultdict(int)

        # all columns are now the same length. Create a list of tuples, where
        # each tuple is a row in this database, i.e., a value from each column in
        # the same position
        data = list()
        for irow in range(maxlen):                      # for all rows
            row = tuple()                               # start with an empty tuple
            for column in self._columns:
                row += (column.get_data()[irow],)       # add this value

            # make sure now no field in this row is "None". This can happen when
            # a cell is empty and no default value was given in the database
            # specification file. These have to be skipped
            if None not in row:

                # register this row
                unique[row] += 1

                # if this row has been inserted before, ...
                if unique[row] > 1:

                    # if check-duplicates was requested
                    if self._context and 'check_duplicates' in self._context:
                        LOGGER.warning(WARNING_DUPLICATED_ROW.format(row))
                    if self._context and 'enforce_unique' in self._context:
                        continue

                # add this tuple and increment the number of accepted rows
                nbrows += 1
                data.append(row)

        # apply now modifiers related to the number of tuples to be generated
        if self._context:
            for imodifier in self._context:
                if imodifier == 'geq':
                    arg = imodifier.get_args()[0]
                    if arg > nbrows:
                        LOGGER.warning(WARNING_LESS.format(nbrows, arg))

                if imodifier == 'leq':
                    arg = imodifier.get_args()[0]
                    if arg < nbrows:
                        LOGGER.warning(WARNING_GREATER.format(nbrows, arg))

                if imodifier == 'eq':
                    arg = imodifier.get_args()[0]
                    if arg != nbrows:
                        LOGGER.warning(WARNING_NOT_EQUAL.format(nbrows, arg))

                if imodifier == 'neq':
                    arg = imodifier.get_args()[0]
                    if arg == nbrows:
                        LOGGER.warning(WARNING_EQUAL.format(nbrows, arg))

        # and return all data retrieved from the spreadsheet in the form of a
        # list of tuples, ready to be inserted into the database
        return data

    def validate(self):
        '''a block is correct if and only if the type of all its columns is known'''

        for column in self._columns:
            if not column.get_type():
                return False

        return True


# -----------------------------------------------------------------------------
# DBSQLStatement
#
# Provides the definition of executable SQL statements
# -----------------------------------------------------------------------------
class DBSQLStatement:
    """
    Provides the definition of a executable SQL statements
    """

    def __init__(self, statement: str):
        '''SQL statements are given as plain strings.

           Importantly, they are executed right there when the (sequential)
           execution flow reaches them. They are executed wrt the database
           specified in the sql statement, i.e., sql statements do not appear
           within any block and therefore the corresponding databse/tables have
           to be fully qualified

        '''

        # copy the attributes
        self._statement = statement

    def __str__(self):
        '''provides a human-readable description of the contents of this SQL
           statement'''

        return " SQL statement: '{0}'\n\n".format(self._statement)


    def get_statement(self):
        """return the SQL statement of this instance"""

        return self._statement


    def exec(self, cursor: sqlite3.Cursor):
        '''executes the SQL statement given to this instance through the specified
           sqlite3 cursor.

           In case an error happend an exception is immediately raised

        '''

        cursor.execute(self._statement)


# -----------------------------------------------------------------------------
# DBTable
#
# Provides the definition of a database table
# -----------------------------------------------------------------------------
class DBTable:
    """
    Provides the definition of a database table
    """

    def __init__(self, name: str,
                 spreadsheet: str, sheetname: str, block: DBBlock):
        '''initializes a database table with the contents of a single block. A block is
           a consecutive definition of different columns. A DBTable is used to
           populate a sqlite3 database with information retrieved from the given
           spreadsheet and sheetname ---and if no sheetname is given, then from
           the first one found by default.

        '''

        # copy the attributes
        self._name, self._block = name, block
        self._spreadsheet, self._sheetname = spreadsheet, sheetname


    def __str__(self):
        '''provides a human-readable description of the contents of this database'''

        output = str()
        output += " Block      : {0}\n".format(self._name)
        output += " Spreadsheet: {0}\n".format(self.get_spreadsheet())
        output += " Sheet name : {0}\n\n".format(self.get_sheetname())
        output += " {0}\n\n".format(self._block)

        return output

    def get_block(self):
        """return the block of this table"""

        return self._block


    def get(self, position=-1):
        '''if no position is given, it returns the list of columns of the block in this
           instance. In case a non-negative value is provided as a position,
           then it returns the column in that position

        '''

        if position < 0:
            return self._block.get_columns()
        return self._block.get_columns()[position]

    def get_name(self):
        '''returns the name of this table'''

        return self._name

    def get_spreadsheet(self):
        '''returns the name of the spreadsheet used to read data from'''

        if not self._spreadsheet:
            return "User defined (default)"
        return self._spreadsheet

    def get_sheetname(self):
        '''returns the sheet name used to read data from'''

        if not self._sheetname:
            return "First one (default)"
        return self._sheetname

    def create(self, cursor: sqlite3.Cursor, append=False):
        '''creates a sqlite3 database table with the schema of its block with the given
           name using the given sqlite3 cursor

           If append is True, data is added to the database so that tables might
           already exist; otherwise, an error is raised in case the same table
           already exists.

        '''

        # first of all, verify whether this table exists or not
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        if(self._name,) in cursor.fetchall():

            # if append is false, then this should be considered as an error;
            # otherwise, it is not an error, and there is no need to create it
            # as it already exists
            if not append:
                LOGGER.error(ERROR_TABLE_EXISTS.format(self._name))
                raise ValueError(ERROR_TABLE_EXISTS.format(self._name))

        else:

            # -- table creation

            # recreate the SQL statement that creates this table
            cmdline = 'CREATE TABLE ' + self._name + ' ('
            for column in self._block.get_columns()[:-1]:        # for all columns but the last one
                cmdline += column.get_name() + ' '               # compose the name of the column
                cmdline += column.get_type() + ', '              # its type and a comma

            # do the same with the last one but with a closing parenthesis instead
            cmdline += self._block.get_columns()[-1].get_name() + ' '
            cmdline += self._block.get_columns()[-1].get_type()

            # verify whether this table has keys or not
            if self._block.get_nbkeys() > 0:

                # add the first primary key as there is surely one at least
                cmdline += ', PRIMARY KEY (' + self._block.get_keys()[0].get_name()

                # and add others in case there are more
                for ikey in self._block.get_keys()[1:]:
                    cmdline += ', ' + ikey.get_name()

                # and close the opening parenthesis listing the primary keys
                cmdline += ')'

            # now, in case this table have any UNIQUE constraints defined, add
            # them after the columns
            if self._block.get_nbuniques() > 0:

                # add the SQL UNIQUE constraint along with the first column
                cmdline += ', UNIQUE (' + self._block.get_uniques()[0].get_name()

                # and add others in case there are more
                for iunique in self._block.get_uniques()[1:]:
                    cmdline += ', ' + iunique.get_name()

                # and close the opening parenthesis listing all UNIQUE
                # constraints
                cmdline += ')'

            # end the SQL statement
            cmdline += ");"

            # and now, create the table
            cursor.execute(cmdline)

            # -- index creation

            # only in case this table contains any indexes
            if self._block.get_indexes():

                # initialize the cmdline
                cmdline = "CREATE INDEX {} ON {} (".format(self._name + "_index", self._name)

                # add the first column, note that at least one is guaranteed to
                # exist
                cmdline += self._block.get_indexes()[0].get_name()

                # and now add others if more than one was given
                for iindex in self._block.get_indexes()[1:]:
                    cmdline += ", {}".format(iindex.get_name())

                # and end the list of indexes
                cmdline += ');'

                # and now, add the key
                cursor.execute(cmdline)


    def insert(self, cursor: sqlite3.Cursor,
               spsname: str, sheetname=None, override=False):
        '''insert the data of this table in a sqlite3 database through the given sqlite3
           cursor. Data is retrieved from the given spreadsheet and sheetname
           which are computed as follows:

           If a spreadsheet name is given, then the specified spreadsheet is
           used provided that none appears in the configuration file, unless
           override is True, i.e., the configuration file has precedence unless
           override is True.

           If a sheetname is given, then the specified sheetname is accessed
           provided that none appears in the configuration file, unless override
           is True. If none is specified, the first sheet found in the
           spreadsheet is used, i.e., the configuration file has precedence
           unless override is True; if none is given anywhere, the first sheet
           found in the spreadsheet is used by default.

        '''

        # create first the specification line to insert data into the sqlite3
        # database, which is derived from the schema of its first block
        specline = "?, " *(len(self._block.get_columns()) - 1)
        cmdline = "INSERT INTO %s VALUES (%s)" % (self._name, specline + '?')

        # compute the right spreadsheet and sheetnames to use. If override is
        # given, then the values specified shall be used
        if not override:

            # If a spreadsheet name or a sheet name were given during the creation
            # of the table in the configuration, use those; otherwise use the
            # specified parameters
            spsname = self._spreadsheet if self._spreadsheet else spsname
            sheetname = self._sheetname   if self._sheetname else sheetname

        # it might happen here that no spreadsheet has been found,
        if not spsname:
            LOGGER.error(ERROR_NO_SPREADSHEET)
            raise ValueError(ERROR_NO_SPREADSHEET)

        # retrieve now data from the spreadsheet (and/or the given sheetname)
        # for the block in this table
        data = self._block.lookup(spsname, sheetname)

        # and insert data
        cursor.executemany(cmdline, data)


# -----------------------------------------------------------------------------
# DBDatabase
#
# Provides the definition of a database as a collection of tables and SQL
# statements
# -----------------------------------------------------------------------------
class DBDatabase:
    """Provides the definition of a database as a collection of tables and SQL
    statements

    """

    def __init__(self, expressions: list):
        '''initializes a database with a list of expressions which shall be instances of
           DBTable and/or SQL statements, given as instances of DBSQLStatement

        '''

        self._expressions = expressions

        # init the counter for iterating over expressions
        self._current = 0

        # other members are now intialized empty
        self._dbname = None
        self._conn = None
        self._cursor = None

    def get(self, position=-1):
        '''if no position is given, it returns the list of expressions (both tables and
           SQL statements) of this instance. In case a non-negative value is
           provided as a position, then it returns the expression in that
           position

        '''

        if position < 0:
            return self._expressions
        return self._expressions[position]

    def __add__(self, other):
        '''extends this database with the expressions found in another database'''

        self._expressions += other._expressions
        return self

    def __iter__(self):
        '''defines the simplest case for iterators'''

        return self

    def __next__(self):
        '''returns the next expression in the definition of this database

        '''

        # if we did not reach the limit
        if self._current < len(self._expressions):

            # return the expression in the current position (after incrementing)
            expr = self._expressions[self._current]

            self._current += 1                  # increment the counter
            return expr                         # and return this one

        # restart the iterator for subsequent invocations of it
        self._current = 0

        # and stop the current iteration
        raise StopIteration()

    def __str__(self):
        '''provides a human-readable description of the contents of this database'''

        output = str()
        for expression in self._expressions:
            output += "{0}".format(expression)

        return output

    def create(self, dbname: str, append=False):
        '''creates a sqlite3 database named 'databasename' with the schema of all tables
           in this instance

           If append is given, then all data extracted is added to the specified
           database tables. Otherwise, an error is issued in case a database is
           found with the same name

        '''

        # make sure no file exists with the same name
        if os.access(dbname, os.F_OK):
            LOGGER.error(ERROR_FILE_EXISTS.format(dbname))
            raise ValueError(ERROR_FILE_EXISTS.format(dbname))

        # create a connection to the database
        self._dbname = dbname                  # store the name of the database
        self._conn = sqlite3.connect(dbname)   # connect to this database
        self._cursor = self._conn.cursor()     # and get a cursor

        # create all tables in this database
        for expression in self._expressions:   # for all expressions

            # only in case this is a table, create it. Otherwise skip it!
            if isinstance(expression, DBTable):
                expression.create(self._cursor, append)

        # close the database
        self._conn.commit()                    # commit all changes
        self._conn.close()                     # close the database

    def insert(self, dbname: str,
               spsname: str, sheetname=None,
               override=False):
        '''inserts data from the given spreadsheet into the sqlite3 database named
           'databasename' according to the schema of all tables in this
           instance, and executes the specified SQL statements. Both insertions
           and executions are performed in precisely the same order they are
           given in the database specification file

           If a spreadsheet name is given, then the specified spreadsheet is
           used provided that none appears in the configuration file, unless
           override is True, i.e., the configuration file has precedence unless
           override is True.

           If a sheetname is given, then the specified sheetname is accessed
           provided that none appears in the configuration file, unless override
           is True. If none is specified, the first sheet found in the
           spreadsheet is used, i.e., the configuration file has precedence
           unless override is True; if none is given anywhere, the first sheet
           found in the spreadsheet is used by default.

        '''

        # create a connection to the database
        self._dbname = dbname                   # store the name of the database
        self._conn = sqlite3.connect(dbname)    # connect to this database
        self._cursor = self._conn.cursor()      # and get a cursor

        # process all expressions in this database
        for expression in self._expressions:

            # if and only if this is a table,
            if isinstance(expression, DBTable):

                # insert data into this table as commanded
                LOGGER.info("* Block {0}".format(expression.get_name()))
                expression.insert(self._cursor, spsname, sheetname, override)

            # if and only if this is a SQL statement
            if isinstance(expression, DBSQLStatement):

                # then execute it within the context of this database
                LOGGER.info("* SQL statement {0}".format(expression.get_statement()))
                expression.exec(self._cursor)

        # close the database
        self._conn.commit()                    # commit all changes
        self._conn.close()                     # close the database


# Local Variables:
# mode:python
# fill-column:80
# End:
