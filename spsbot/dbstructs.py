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
import os                               # access
import sqlite3
import sys                              # exit

import pyexcel

from . import structs

# globals
# -----------------------------------------------------------------------------

# -- errors
ERROR = " Error - {0}"
ERROR_CAST_COLUMN = "It was not possible to cast the default value '{0}' defined for column '{1}' to the type '{2}'"
ERROR_CAST_DBCOLUMN = "It was not possible to cast the value '{0}' in database '{1}::{2}' to the type {3}"
ERROR_CAST_CELL = "It was not possible to cast the value '{0}' found in cell {1} in database '{2}::{3}' to the type {4}"
ERROR_EXTENT = "It is not possible to extend column '{0}' which contains {1} items to hold {2} items"
ERROR_NO_DATA = "No data was found in cell '{0}' in database '{1}::{2}'"
ERROR_CONTENT_UNKNOWN_TYPE = "Unknown type for content {0}"
ERROR_DIFF_BLOCKS = """The block
{0}

is not equal to the block

{1}"""
ERROR_BLOCK_UNSPECIFIED_TYPE = """
The block

{0} contains columns with unspecified types"""
ERROR_TABLE_EXISTS = " Table '{0}' already exists"
ERROR_NO_SPREADSHEET = " No spreadsheet has been given"
ERROR_FILE_EXISTS = " The file '{0}' already exists!"

# -- warnings
WARNING = " Warning - {0}"

# -- literals
STR_DBCOLUMN = "\t Name  : {0}\n\t Contents : {1}\n\t Type  : {2}\n\t Action: {3}"


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

    def __init__(self, action, default=None):

        '''an action consists of either ignoring (None), warning or issuing an
error. Additionally, in the first two cases, default values shall be specified

        '''

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

    def handle_action(self, name, ctype, message=''):
        '''applies this action to a column named "name" which is defined to store values
           of the specified type. It returns the data to be used with the correct type

        '''

        # apply the action specified in this instance
        if self._action == 'Error':                             # in case of error

            # issue a message and exit
            print(ERROR.format(message))
            sys.exit(0)

        elif self._action == 'Warning':                         # in case of warning

            # show a warning message and use the default value defined for this
            # column
            print(WARNING.format(message))
            data = self._default

        # if it is neither an error mpr a warning, silently copy the default
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
                elif ctype == 'text':
                    data = str(data)

            except:

                # if it was not possible then exit with an error
                print(ERROR_CAST_COLUMN.format(data, name, ctype))
                sys.exit(0)

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
           numbers and strings) is defined explicitly just by providing it.

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
# DBContents
#
# Definition of a collection of contents which can be either ranges of cells or
# contents explicitly given. This container provides an iterator
# -----------------------------------------------------------------------------
class DBContents:
    """Definition of a collection of contents which can be either ranges of cells
    or contents explicitly given. This container provides an iterator

    """

    def __init__(self, intervals):
        '''defines a list of intervals, each of the form [start, end]. All intervals
           should be instances of Range

        '''

        # copy the given intervals
        self._intervals = intervals

        # initialize the information used by the iterator
        self._ith = 0                           # _ith stores the current interval

    def __str__(self):
        '''provides a human readable representation of the contents of this intance'''

        output = str()
        for interval in self._intervals:
            output += "{0}; ".format(interval)

        return output

    def __add__(self, other):
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

    def __init__(self, name, contents, ctype, action):
        '''defines a column with the given name which should be populated with the
           specified contents. Contents can be either ranges of cells whose
           value has to be retrieved from the database or data explicitly given

           All data read should be automatically casted into the given ctype. In
           case a cell contains no data, the specified action should be raised

        '''

        # copy the attributes given to the constructor
        self._name, self._contents, self._type, self._action = (name, contents, ctype, action)

        # and also intialize the container which should store the data retrieved
        # from the spreadsheet
        self._data = list()

    def __eq__(self, other):
        '''a column is equal to another if and only if they have the same name in spite
           of all the other attributes'''

        return self._name == other._name

    def __str__(self):
        '''provides a human-readable description of the contents of this column'''

        return STR_DBCOLUMN.format(self._name, self._contents, self._type, self._action)

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

            print(ERROR_EXTENT.format(self._name, len(self._data), length))
            sys.exit(0)

        # and return the new container
        return self._data


    def lookup(self, spsname, sheetname=None):
        '''returns the contents of this column. If it consists of data explicitly given,
           then it return it right away after casting it to the appropriate
           type; if the contents of this column consist of ranges of cells, then
           it access the spreadsheet to retrieve them

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
            elif isinstance(content, structs.Range):

                # first, gain access to the spreadsheet
                if not sheetname:
                    sheet = pyexcel.get_sheet(file_name=spsname)
                    sheetname = sheet.name          # and copy the first sheet's name
                else:
                    sheet = pyexcel.get_sheet(file_name=spsname, sheet_name=sheetname)

                # now, for all cells in this range
                for cell in content:

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

                raise TypeError(ERROR_CONTENT_UNKNOWN_TYPE.format(content))

        # and return the result
        return self._data


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

    def __init__(self, columns):
        '''initializes a database table with the given name and information from all the
        given columns, which shall be instances of DBColumn reading data from
        the given sheetname in the specified spreadsheet

        '''

        # copy the attributes
        self._columns = columns

    def get_columns(self):
        """return the columns of this block"""

        return self._columns

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
        for column in self._columns:
            output += "{0}\n\n".format(column)

        return output                           # return the output string

    def lookup(self, spsname, sheetname=None):
        '''looks up the given spreadsheet and returns a list of tuples to insert in a
           sqlite3 database. If a sheetname is given, then it access that
           specified sheet; otherwisses, it uses the first one.

        '''

        # --- initialization
        maxlen = 0                      # length of the longest column

        # iterate over all columns to look up the spreadsheet
        for column in self._columns:

            print(" \t > Looking up column {0}".format(column.get_name()))

            # look up this specific table
            column.lookup(spsname, sheetname)
            maxlen = max(maxlen, len(column.get_data()))

        # now, make sure that all columns have the same length
        for column in self._columns:

            column.extend(maxlen)

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
                data.append(row)                       # and add this tuple

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

    def __init__(self, statement):
        '''SQL statements are given as plain strings. Importantly, they are executed
           right there when the (sequential) execution flow reaches'em. They
           are executed wrt the database specified.

        '''

        # copy the attributes
        self._statement = statement

    def __str__(self):
        '''provides a human-readable description of the contents of this SQL
           statement'''

        return " SQL statement: '{0}'\n\n".format(self._statement)


    def exec(self, cursor):
        '''executes the SQL statement given to this instance through the specified sqlite3 cursor.

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

    def __init__(self, name, spreadsheet, sheetname, columns):
        '''initializes all blocks of a database table with the given name from the given
           columns which should be a list of instances of DBColumn. A block is a
           consecutive definition of different columns. A DBTable is used to
           populate a sqlite3 database with information retrieved from the given
           spreadsheet and sheetname ---and if no sheetname is given, then from
           the first one found by default.

        '''

        # copy the attributes
        self._name, self._columns = name, columns
        self._spreadsheet, self._sheetname = spreadsheet, sheetname

        # a block consists of a consecutive definition of different
        # columns. Thus, the given columns should be examined: if all of them
        # are different then only one block should be constructed; if a column
        # is repeated, a new block should be built. All blocks should contain
        # columns in precisely the same order.

        # initialize the list of blocks in this table
        self._blocks = list()

        # at least, the first column belongs to the first block
        curr = [self._columns[0]]

        # for all the other columns
        icolumn = 0
        while icolumn < len(self._columns) - 1:

            # if the next column is already in the current block
            if self._columns[1 + icolumn] in curr:

                # then the current block should be ended
                self._blocks.append(DBBlock(curr))

                # and initialize again the current block
                icolumn += 1
                curr = [self._columns[icolumn]]

            else:

                # otherwise, this column should be added to the current block
                curr.append(self._columns[1 + icolumn])

                # and move to the next column
                icolumn += 1

        # at this point, curr should contain the last block which should be
        # added to the list of blocks of this table
        self._blocks.append(DBBlock(curr))

        # verify now that all blocks are equal, i.e., that they contain the same
        # columns (with the same name) in precisely the same order
        for iblock in range(len(self._blocks) - 1):

            if self._blocks[iblock] != self._blocks[1+iblock]:

                raise ValueError(ERROR_DIFF_BLOCKS.format(self._blocks[iblock],
                                                          self._blocks[1+iblock]))

        # finally, the first block should be correct, i.e., the type of all its
        # columns should have been specified, since that is the specific block
        # to use for both creating the table and inserting data into it
        if not self._blocks[0].validate():
            raise TypeError(ERROR_BLOCK_UNSPECIFIED_TYPE.format(self._blocks[0]))


    def __str__(self):
        '''provides a human-readable description of the contents of this database'''

        output = str()                         # initialize the output string
        output += " Name: {0}\n".format(self._name)
        output += " Spreadsheet: {0}\n".format(self.get_spreadsheet())
        output += " Sheet name : {0}\n\n".format(self.get_sheetname())

        for block in self._blocks:
            output += "{0}\n".format(block)

        return output                           # return the output string

    def get_blocks(self):
        """return the number of blocks of this table"""

        return self._blocks


    def get(self, position=-1):
        '''if no position is given, it returns the list of columns of this instance. In
           case a non-negative value is provided as a position, then it returns
           the column in that position

        '''

        if position < 0:
            return self._columns
        return self._columns[position]

    def get_name(self):
        '''returns the name of this table'''

        return self._name

    def get_spreadsheet(self):
        '''returns the name of the spreadsheet used to read data from'''

        if not self._spreadsheet:
            return "user defined"
        return self._spreadsheet

    def get_sheetname(self):
        '''returns the sheet name used to read data from'''

        if not self._sheetname:
            return "first one (default)"
        return self._sheetname

    def create(self, cursor, append=False):
        '''creates a sqlite3 database table with the schema of its first block with the
           given name using the given sqlite3 cursor

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
                raise ValueError(ERROR_TABLE_EXISTS.format(self._name))

        else:

            cmdline = 'CREATE TABLE ' + self._name + ' ('
            for column in self._blocks[0].get_columns()[:-1]:    # for all columns but the last one
                cmdline += column.get_name() + ' '               # compose the name of the column
                cmdline += column.get_type() + ', '              # its type and a comma

            # do the same with the last one but with a closing parenthesis instead
            cmdline += self._blocks[0].get_columns()[-1].get_name() + ' '
            cmdline += self._blocks[0].get_columns()[-1].get_type() + ')'

            # and now, create the table
            cursor.execute(cmdline)

    def insert(self, cursor, spsname, sheetname=None, override=False):
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
        specline = "?, " *(len(self._blocks[0].get_columns()) - 1)
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

            raise ValueError(ERROR_NO_SPREADSHEET)

        # retrieve now data from the spreadsheet (and/or the given sheetname)
        # for each block in this table
        data = list()
        for block in self._blocks:
            data += block.lookup(spsname, sheetname)

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

    def __init__(self, expressions):
        '''initializes a database with the given tables which shall be instances of
           DBTable and SQL statements, given as instances of DBSQLStatement

        '''

        self._expressions = expressions
        self._current = 0               # used to iterate over expressions

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

        output = str()                         # initialize the output string
        for expression in self._expressions:
            output += "{0}".format(expression) # format each expression

        return output                          # and return the string

    def create(self, dbname, append=False):
        '''creates a sqlite3 database named 'databasename' with the schema of all tables
           in this instance

           If append is given, then all data extracted is added to the specified
           database tables. Otherwise, an error is issued in case a database is
           found with the same name

        '''

        # make sure no file exists with the same name
        if os.access(dbname, os.F_OK):
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

    def insert(self, dbname, spsname, sheetname=None, override=False, append=False):
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

           If append is given, then all data extracted is added to the specified
           database tables. Otherwise, an error is issued in case a database is
           found with the same name

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
                expression.insert(self._cursor, spsname, sheetname, override)

            # if and only if this is a SQL statement
            if isinstance(expression, DBSQLStatement):

                # then execute it within the context of this database
                expression.exec(self._cursor)

        # close the database
        self._conn.commit()                    # commit all changes
        self._conn.close()                     # close the database


# Local Variables:
# mode:python
# fill-column:80
# End:
