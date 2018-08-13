#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# spsstructs.py
# Description: Definition of all classes required to represent the
# information parsed from a sps file
# -----------------------------------------------------------------------------
#
# Started on  <Thu Jul 12 15:42:50 2018 >
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
Definition of all classes required to represent the information parsed from a sps file
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.0'


# imports
# -----------------------------------------------------------------------------
import pyexcel
import sqlite3

import structs

# classes
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# DynamicArray
#
# Definition of a (pontentially) inifinite two-dimensional array
# indexed by spreadsheet cells
# -----------------------------------------------------------------------------
class DynamicArray:
    """Definition of a (pontentially) inifinite two-dimensional array indexed by
       spreadsheet cells

    """

    def __init__ (self):

        '''creates an empty two-dimensional array

        '''

        # initializes the private two-dimensional array
        self._data = [[]]

    def __getitem__ (self, key):
        '''return the evaluation of self[key], where key is a cell name such as
           D4. First row is A, and first column is 1

        '''

        # process the key to get both the row and column
        (col, row) = structs.get_columnrow (key)

        # translate now the column into a unique integer identifier
        # corresponding to its position (where 'A' is 0)
        column = structs.get_columnindex (col)

        # return the value at the given location provided that the key is within
        # the range of this dynamic array
        if row <= len (self._data):

            if column < len (self._data [row-1]):

                return self._data[row-1][column]

            else:
                raise IndexError

        else:
            raise IndexError

    def __setitem__ (self, key, value):
        '''set the value of the position corresponding to the given key with the
           specified content. If necessary, the two-dimensional array is
           extended to insert the new value

        '''

        # process the key to get both the row and column
        (col, row) = structs.get_columnrow (key)

        # translate now the column into a unique integer identifier
        # corresponding to its position (where 'A' is 0)
        column = structs.get_columnindex (col)

        # randomly access the specified row
        if row <= len (self._data):

            # and also randomly access the specified column within this row
            if column < len (self._data [row-1]):

                # insert the value
                self._data [row-1][column] = value

            else:                       # if this column goes beyond the current size

                # create extra columns and add them to the coresponding row
                extracols = [None]*(1+column-len (self._data[row-1]))
                self._data [row-1].extend (extracols)

                # and try the insertion again
                self.__setitem__ (key, value)

        else:                           # if this row goes beyond the current size

            # add as many empty rows as necessary
            for irow in range (row-len (self._data)):
                self._data.extend ([[]])

            # and make now the insertion
            self.__setitem__ (key, value)

    def rows (self):
        '''return the number of rows in the two-dimensional array'''

        return len (self._data)

    def columns (self, row):
        '''return the number of columns in the given row. The first row index should be 1'''

        return len (self._data[row-1])

    def get_data (self):
        '''return the two-dimensional array of this instance'''

        return self._data
            

# -----------------------------------------------------------------------------
# SPSCommand
#
# Definition of a basic command
# -----------------------------------------------------------------------------
class SPSCommand:
    """Definition of a basic command

    """

    def __init__ (self, name, crange, ctype, text):

        '''a command consists of writing data into the spreadsheet in the given range,
           given as an instance of Range. Commands are characterized by their
           type (either writing literals or the result of a query), and the
           string with either the string to literally insert or the query to
           execute. Commands can be identified by their name but they are not
           forced to be given a name

           This is the base class of all type of commands

        '''

        self._name, self._range, self._type, self._text = name, crange, ctype, text

    def get_name (self):
        '''return the name of this command'''

        return self._name

    def get_range (self):
        '''return the range of this command'''

        return self._range

    def get_type (self):
        '''return the type of this command'''

        return self._type

    def get_text (self):
        '''return the text of this command'''

        return self._text

        
# -----------------------------------------------------------------------------
# SPSLiteral
#
# Definition of a command which consists of inserting literals
# -----------------------------------------------------------------------------
class SPSLiteral (SPSCommand):
    """Definition of a command which consists of inserting literals

    """

    def __init__ (self, name, crange, text, direction=None):
        '''a literal consists of inserting the given text in an arbitrary number of
           cells. In case a direction is given the command replicates the
           literal in the given direction

           Even if a direction is given, it is ignored for literals

        '''

        # create an instance invoking the constructor of the base class
        super (SPSLiteral, self).__init__(name=name, crange=crange, ctype='literal', text=text)
        self._direction = direction
        
    def __str__ (self):
        '''provides a human readable representation of the contents of this intance'''

        if self._name:
            return "Literal '{0}' with contents '{1}' in range {2}".format (self._name, self._text, self._range)
        return "Explicit literal with contents '{0}' in range {1}".format (self._text, self._range)

    def execute (self, data):
        '''executes this literal updating the contents of the given array

        '''

        # for all cells in the given array
        for cell in self._range:

            # insert this literal
            data[cell] = self._text

        # and return the contents created by the execution of this litral
        return data
    
        
# -----------------------------------------------------------------------------
# SPSQuery
#
# Definition of a command which consists of inserting the result of a
# sql query
# -----------------------------------------------------------------------------
class SPSQuery (SPSCommand):
    """Definition of a command which consists of inserting the result of a sql query

    """

    def __init__ (self, name, crange, text, dbref = None, direction=None):
        '''a query consists of inserting the result of a sql query in an arbitrary
           number of cells from a given database if provided ---otherwise, it
           will be computed later. As there might be an arbitrary number of
           results, all tuples are inserted in the given direction. However, it
           is assumed by default that the result of the query consists of a
           single tuple and thus, there is no direction.

        '''

        # create an instance invoking the constructor of the base class
        super (SPSQuery, self).__init__(name=name, crange=crange, ctype='query', text=text)
        self._dbref = dbref
        self._direction = direction
        
    
    def __str__ (self):
        '''provides a human readable representation of the contents of this intance'''

        if self._direction:
            return "Query '{0}' with contents '{1}' in range {2} with direction {3}".format (self._name, self._text, self._range, self._direction)
        return "Query '{0}' with contents '{1}' in range {2}".format (self._name, self._text, self._range)

    def get_direction (self):
        '''return the direction of this command'''

        return self._direction

    def get_dbref (self):
        '''return the specific database to use when executing this query'''

        return self._dbref

    def execute (self, data, dbname=None):
        '''executes the result of this query by updating the contents of the given array
           using the given database unless this query has been created wrt a
           specific database. In this case, that specific database is used
           instead

           Note it is possible to provide no database as this query might
           contain a reference to the database to use which can not be overriden
           by any directive.

        '''

        # initialization - get the current range
        rnge = self._range

        # if this query has been defined with regard to a specific database then
        # use that one; otherwise, use the given database and raise an error if
        # none can be found
        dbref = self._dbref if self._dbref else dbname
        if not dbref:
            raise ValueError ("""Fatal error - No database has been found for executing the following query:
 {0}""".format (self))

        # get a cursor to it
        conn = sqlite3.connect (dbref)
        cursor = conn.cursor ()
                    
        # query the database
        cursor.execute (self._text[1:-1])
        result = cursor.fetchall ()

        # for all tuples in the result of the query
        for value in result:

            # and for all cells in the range of this instance
            for i, cell in enumerate(rnge):

                # write the index-th value of this tuple in this cell
                data [cell] = value[i]

            # update the range by sliding it in the given direction
            if self._direction == 'down':
                rnge = rnge.add_rows (rnge.number_of_rows ())
            else:
                rnge = rnge.add_columns (rnge.number_of_columns ())

        # and return the new data
        return data
    
        
# -----------------------------------------------------------------------------
# SPSRegistry
#
# A registry consists of a sequence of commands which should be
# executed in precisely the same order
# -----------------------------------------------------------------------------
class SPSRegistry:
    """A registry consists of a sequence of commands which should be
       executed in precisely the same order

    """

    def __init__ (self, command=None):
        '''when creating a registry either a command or none has to be given. Commands should be given as instances of SPSCommand (or any of its subtypes)

        '''

        # init the list of commands if any is given
        self._registry = []
        if command:
            self._registry.append (command)

        # also init the private counter used for iterating the registry
        self._ith = 0        
    
    def __add__ (self, other):
        '''extends this registry with all commands in the other registry'''

        self._registry += other._registry
        return self
    
    def __iter__ (self):
        '''defines the simplest case for iterators'''
        
        return self

    def __next__ (self):
        '''returns the next command in this registry

        '''

        # if we did not reach the limit
        if self._ith < len (self._registry):

            # return the current command after incrementing the
            # private counter
            command = self._registry [self._ith]
            self._ith += 1
            return command
            
        else:
            
            # restart the iterator for subsequent invocations of it
            self._ith = 0

            # and stop the current iteration
            raise StopIteration ()

    def __str__ (self):
        '''provides a human readable representation of the contents of this intance'''

        output = str ()
        for command in self._registry:
            output += "{0}\n".format (command)

        return output

    def execute (self, dbname=None):
        '''executes all commands in this registry from data in the given
           database if any is given and returns an array of contents
           to insert into the spreadsheet

        '''

        # initialize a dynamic array to store all contents created by
        # the execution of all commands in this registry
        contents = DynamicArray ()

        # for all commands in this registry
        for command in self._registry:

            # add the contents created by the execution of this command
            if command.get_type () == 'literal':                # literals do not 
                contents = command.execute (contents)           # need databases
            else:                                               # but queries
                contents = command.execute (contents, dbname)   # do

        # return all contents
        return contents
    
    
# -----------------------------------------------------------------------------
# SPSSpreadsheet
#
# A spreadsheet consists of a registry with commands that shall be
# executed over a given spreadsheet and sheet using data from a
# reference database
# -----------------------------------------------------------------------------
class SPSSpreadsheet:
    """A spreadsheet consists of a registry with commands that shall be
       executed over a given spreadsheet and sheet using data from a
       reference database

    """

    def __init__ (self, registry, spsname = None, sheetname = None, dbref = None):
        '''An instance of SPSRegistry has to be given to create the contents
of a spreadsheet. The combination spreadsheet filename/sheet name and
the reference database to use are not mandatory as these could be
supplied by other means.

        '''

        # copy the arguments
        self._registry = registry
        self._spsname, self._sheetname = spsname, sheetname
        self._dbref = dbref

    def __str__ (self):
        '''provides a human readable representation of the contents of this intance'''

        output = str ()
        output += " Spreadsheet: {0}\n".format (self._spsname if self._spsname else "<Unknown>")
        output += " Sheet name : {0}\n".format (self._sheetname if self._sheetname else "<Unknown>")
        output += " Database   : {0}\n".format (self._dbref if self._dbref else "<Unknown>")
        output += " Registry   :\n{0}".format (self._registry)

        return output

    def execute (self, dbname = None, spsname = None, sheetname = None, override=False):
        '''executes all commands in the registry of this spreadsheet
           effectively inserting data into the given spreadsheet/sheet
           name from data in the given database if any is provided.

           If the database is not given, then it is retrieved from the
           configuration file. If it exists in the configuration file but is
           given here with override=True then the one given here is used
           instead. The same rule applies to the name of the spreadsheet to
           create and also the sheet name. The only exception is that if it is
           not possible to determine a dbname/spsname, an exception is raise; if
           it is not possible to determine a spreadsheet name, then the first
           one is used by default.

           Note that all parameters are optional. If they are not
           given, then they should be supplied in the configuration
           file.

        '''

        def _default_handler (external, internal, msg=None):
            '''determine the default value to use from two different values: an external
            value and an internal value. If necessary, "override" is used to
            solve ties. In case it is not possible to compute a value, raise an
            error only in case a message is given

            '''
            if not internal:                            # if no internal value is known
                value = external                        # take the specified by the user
            elif not external:                          # if no value is specified by the user
                value = internal                        # take the internal one
            else:                                       # if both are given
                value = external if override else internal      # use override to decide
            if msg and not value:                       # if no value was found and a msg is given
                raise ValueError ("""Fatal error - {0}:
 {1}""".format (msg, self._registry))                     # raise an error

            return value                                # and return the value computed so far
            
        # first of all, determine the db, spreadsheet and sheetname to use

        # --dbref
        dbref = _default_handler (dbname, self._dbref, "No database was given to execute the following commands")

        # --spsname
        spsref = _default_handler (spsname, self._spsname, "No spreadsheet was given to store the results of executing the following commands")

        # --sheetname
        sheetnameref = _default_handler (sheetname, self._sheetname)

        # and now execute all commands in the current registry. The result is an
        # array of contents to insert into the spreadsheet
        contents = self._registry.execute (dbref)

        # get an instance of the sheet that has to be created accessed
        sheet = pyexcel.Sheet (contents.get_data ())

        print (sheet)
        
        # finally save the contents of this sheet into the given file. If not
        # sheetname was given, then use the first one by default
        if sheetnameref:
            sheet.name = sheetnameref
            sheet.save_as (spsref)
        else:
            sheet.save_as (spsref)
            

# -----------------------------------------------------------------------------
# SPSDeck
#
# A deck consists of a list of spreadsheets
# -----------------------------------------------------------------------------
class SPSDeck:
    """A deck consists of a list of spreadsheets

    """

    def __init__ (self, sps = None):
        '''A table can be created empty but, if given, it is initialized with
           an instance of SPSSpreadsheet

        '''

        # init the deck if a spreadsheet is given
        self._deck = []
        if sps:
            self._deck.append (sps)

        # also init the private counter used for iterating
        self._ith = 0        
    
    def __add__ (self, other):
        '''extends this deck with all spreadsheets in a different table'''

        self._deck += other._deck
        return self
    
    def __iter__ (self):
        '''defines the simplest case for iterators'''
        
        return self

    def __next__ (self):
        '''returns the next spreadsheet in this deck

        '''

        # if we did not reach the limit
        if self._ith < len (self._deck):

            # return the current spreadsheet after incrementing the
            # private counter
            sps = self._deck [self._ith]
            self._ith += 1
            return sps
            
        else:
            
            # restart the iterator for subsequent invocations of it
            self._ith = 0

            # and stop the current iteration
            raise StopIteration ()

    def __str__ (self):
        '''provides a human readable representation of the contents of this intance'''

        output = str ()
        for sps in self._deck:
            output += "{0}\n".format (sps)

        return output

    def execute (self, dbname = None, spsname = None, sheetname = None, override=False):
        '''executes all commands in the registry of all spreadsheets in this
           deck effectively inserting data into the given
           spreadsheet/sheet name from data in the given database if
           any is provided.

           If the database is not given, then it is retrieved from the
           configuration file. If it exists in the configuration file but is
           given here with override=True then the one given here is used
           instead. The same rule applies to the name of the spreadsheet to
           create and also the sheet name.

           Note that all parameters are optional. If they are not
           given, then they should be supplied in the configuration
           file.

        '''

        # for all spreadsheets in this deck
        for sps in self._deck:

            # execute all commands in the registry of this specific
            # spreadsheet
            sps.execute (dbname, spsname, sheetname, override)

            
    
# Local Variables:
# mode:python
# fill-column:80
# End:
