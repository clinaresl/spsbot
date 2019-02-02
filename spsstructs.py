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
import pyexcel                  # reading/writing to various formats of spreadsheets
import xlsxwriter               # writing to xlsx files

import math
import re
import sqlite3
import sys

import structs

# functions
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# get_type
#
# returns the type of its argument, one among [text, integer, real, formula]. If
# the type cannot be derived, it returns 'unknown'
# -----------------------------------------------------------------------------
def get_type (content):
    '''returns the type of its argument, one among [text, integer, real,
    formula]. If the type cannot be derived, it returns 'unknown'

    '''

    if isinstance (content, str):
        return "formula" if content[0] == '=' else "text"
    elif isinstance (content, float):
        return "real"
    elif isinstance (content, int):
        return "integer"
    else:
        return "unknown"


# -----------------------------------------------------------------------------
# drag
# 
# replace the occurrence of each cell not preceded by '$' with a new cell where
# the given offset is applied. The offset is given in the form (<col-offset>,
# <row-offset>)
#
#  Example:
#
#       drag ((+2,-1), "C31 + $D31 + E31")
#
# produces "E30 + $D31 + G30"
# -----------------------------------------------------------------------------
def drag (offset, string):
    '''replace the occurrence of each cell not preceded by '$' with a new cell where
       the given offset is applied. The offset is given in the form
       (<col-offset>, <row-offset>)

       Example:

          drag ((+2,-1), "C31 + $D31 + E31")

       produces "E30 + $D31 + G30"

    '''

    # match any cell name which is not preceded by '$'
    for match in re.finditer (r'(?<!\$)[a-zA-Z]+\d+', string):

        # now, add to this cell the given offset
        cell = structs.add_columns (match.group (), offset[0])
        cell = structs.add_rows (cell, offset[1])

        # and perform the substitution
        string = re.sub (match.group (), cell, string)

    # and return the resulting string
    return string


# -----------------------------------------------------------------------------
# evaluate
#
# Return the string obtained by evaluating the leftmost non-overlapping
# occurrences of pattern in string preceded by '$'and an offset specified
# in the form "+(<number>, <number>)" with the values in replacement repl
# and the given offset. If the pattern isn’t found, string is returned
# unchanged. repl must be a dictionary which specifies, for every feasible
# match, the value that should be used in the substitution.
#
# Example: 
#
#    evaluate (r'[a-zA-Z_]+\.[a-zA-Z_]+\.[a-zA-Z_]+',
#              {'query.personal_data.nw':'B2', 'query.personal_data.sw':'B41'},
#              "=AVERAGE($query.personal_data.nw + (-1,1), $query.personal_data.sw + (4,1))"
#
#    produces "=AVERAGE(A3, F42)"
#
# Note, however, that if more than a dollar sign is given, only the
# rightmost is used in the substitution.
#
# Example:
#
#    evaluate (r'[a-zA-Z_]+\.[a-zA-Z_]+\.[a-zA-Z_]+',
#              {'query.personal_data.nw':'B2', 'query.personal_data.sw':'B41'},
#              "=AVERAGE($query.personal_data.nw + (-1,1), $$query.personal_data.sw + (4,1))"
#
#    (note the "$$" in string)
#
#    produces "=AVERAGE(A3, $F42)"
# -----------------------------------------------------------------------------
def evaluate (pattern, repl, string):
    '''Return the string obtained by evaluating the leftmost non-overlapping
       occurrences of pattern in string preceded by '$'and an offset specified
       in the form "+(<number>, <number>)" with the values in replacement repl
       and the given offset. If the pattern isn’t found, string is returned
       unchanged. repl must be a dictionary which specifies, for every feasible
       match, the value that should be used in the substitution.

       Example: 

          evaluate (r'[a-zA-Z_]+\.[a-zA-Z_]+\.[a-zA-Z_]+',
                    {'query.personal_data.nw':'B2', 'query.personal_data.sw':'B41'},
                    "=AVERAGE($query.personal_data.nw + (-1,1), $query.personal_data.sw + (4,1))"

          produces "=AVERAGE(A3, F42)"

       Note, however, that if more than a dollar sign is given, only the
       rightmost is used in the substitution.

       Example:

          evaluate (r'[a-zA-Z_]+\.[a-zA-Z_]+\.[a-zA-Z_]+',
                    {'query.personal_data.nw':'B2', 'query.personal_data.sw':'B41'},
                    "=AVERAGE($query.personal_data.nw + (-1,1), $$query.personal_data.sw + (4,1))"

          (note the "$$" in string)

          produces "=AVERAGE(A3, $F42)"

    '''

    # for all occurrences of the given pattern which are preceded by the dollar
    # sign and followed by an offset
    for match in re.finditer (r'\$' + pattern + r'\s*\+\s*\(\s*[\+-]?\d+,\s*[\+-]?\d+\)', string):

        # process this occurrence for extracting the variable and the offset
        m = re.match (r'(' + pattern + r')' + r'\s*\+\s*\(\s*([\+-]?\d+),\s*([\+-]?\d+)\)', match.group ()[1:])

        # create now a spscell with the information extracted so far and
        # evaluate the expression with the information given in replacement
        cell = SPSCellReference (m.groups ()[0], int (m.groups ()[1]), int (m.groups ()[2]))
        result = cell.execute (repl)

        # and now simply substitute this match with the result of the evaluation
        # but take special care with the offset: it could be given with the plus
        # sign which should be escaped
        coloffset = r'\+' + m.groups ()[1][1:] if m.groups ()[1][0]=='+' else m.groups ()[1]
        rawoffset = r'\+' + m.groups ()[2][1:] if m.groups ()[2][0]=='+' else m.groups ()[2]
        string = re.sub (r"\${0}\s*\+\s*\(\s*{1},\s*{2}\)".format(m.groups ()[0], coloffset,rawoffset), result, string)

    # and return the resulting string
    return string


# -----------------------------------------------------------------------------
# substitute
#
# Return the string obtained by replacing the leftmost non-overlapping
# occurrences of pattern in string preceded by '$' by the replacement
# repl. If the pattern isn’t found, string is returned unchanged. repl must
# be a dictionary which specifies, for every feasible match, the value that
# should be used in the substitution.
#
# Example: 
#
#    substitute (r'[a-zA-Z]+', {'name': "Alan", 'surname': "Turing"},
#                "My name is $name $surname") 
#    produces "My name is Alan Turing"
#
# Incidentally, if the pattern is preceded of various '$' then all but the
# rightmost are preserved.
#
# Example: 
#
#    substitute (r'[a-zA-Z_]+\.[a-zA-Z_]+\.[a-zA-Z_]+',
#                {'query.personal_data.nw':'B2', 'query.personal_data.sw':'B41'},
#                "=AVERAGE($query.personal_data.nw, $query.personal_data.sw)")
#
#    produces "=AVERAGE(B2, B41)"
#
#    but
#
#    substitute (r'[a-zA-Z_]+\.[a-zA-Z_]+\.[a-zA-Z_]+',
#                {'query.personal_data.nw':'B2', 'query.personal_data.sw':'B41'},
#                "=AVERAGE($$query.personal_data.nw, $$query.personal_data.sw)")
#
#   (note the "$$" in string)
#
#    produces "=AVERAGE($B2, $B41)"
# -----------------------------------------------------------------------------
def substitute (pattern, repl, string):
    '''Return the string obtained by replacing the leftmost non-overlapping
       occurrences of pattern in string preceded by '$' by the replacement
       repl. If the pattern isn’t found, string is returned unchanged. repl must
       be a dictionary which specifies, for every feasible match, the value that
       should be used in the substitution.

       Example: 

          substitute (r'[a-zA-Z]+', {'name': "Alan", 'surname': "Turing"},
                      "My name is $name $surname") 
          produces "My name is Alan Turing"

       Incidentally, if the pattern is preceded of various '$' then all but the
       rightmost are preserved.

       Example: 

          substitute (r'[a-zA-Z_]+\.[a-zA-Z_]+\.[a-zA-Z_]+',
                      {'query.personal_data.nw':'B2', 'query.personal_data.sw':'B41'},
                      "=AVERAGE($query.personal_data.nw, $query.personal_data.sw)")

          produces "=AVERAGE(B2, B41)"

          but

          substitute (r'[a-zA-Z_]+\.[a-zA-Z_]+\.[a-zA-Z_]+',
                      {'query.personal_data.nw':'B2', 'query.personal_data.sw':'B41'},
                      "=AVERAGE($$query.personal_data.nw, $$query.personal_data.sw)")

          (note the "$$" in string)

          produces "=AVERAGE($B2, $B41)"

    '''

    # for all occurrences of the given pattern which are preceded by the dollar
    # sign
    for match in re.finditer (r'\$' + pattern, string):

        # perform the substitution
        string = re.sub ("\${0}".format (match.group ()[1:]), repl[match.group ()[1:]], string)

    # and return the resulting string
    return string

    
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
# SPSCellContent
#
# Definition of contents of an arbitrary cell
# -----------------------------------------------------------------------------
class SPSCellContent:
    """Definition of contents of an arbitrary cell

    """

    def __init__ (self, data, ctype, attributes=None):
        """The contents of a cell are qualified by its data, its type, which should be
           restricted to one among: text, integer, real, formula, (i.e., those
           recognized from the database (but dates) and, additionally, formulae)
           and its attributes which are free-form strings that should be parsed
           by xlsxwriter given as a list, or None if none is given

        """

        # verify that the given type is known, and reject unknown types
        if ctype not in ['text', 'integer', 'real', 'text', 'formula']:
            raise ValueError (" The cell content type '{0}' is not known!".format (ctype))

        # and copy now the attributes
        (self._data, self._type, self._attributes) = (data, ctype, attributes)

    def get_data (self):
        """ returns the contents of this cell"""

        return self._data

    def get_type (self):
        """ returns the type of contents of this cell"""

        return self._type

    def get_attributes (self):
        """ return a list with the (xlsxwriter) attributes of this cell"""

        return self._attributes        
        

# -----------------------------------------------------------------------------
# SPSCellReference
#
# Definition of a cell given either explicitly or with variables and an optional
# offset
# -----------------------------------------------------------------------------
class SPSCellReference:
    """Definition of a cell given either explicitly or with variables and an
       optional offset

    """

    def __init__ (self, descriptor, coloffset=0, rowoffset=0):
        """A cell can be defined either explicitly, e.g., H27, or with a variable, e.g.,
           query.personal_data.sw. Additionally, it can be defined with an
           offset in colummns and rows

           If a cell is created explicitly, then its location is perfectly known
           even if a non-null offset is given. However, if it is declared wrt a
           variable, then a context is required to compute its location.

        """

        self._descriptor, self._coloffset, self._rowoffset = descriptor, coloffset, rowoffset

        # by default the location of this cell is unknown until the execution
        # method is invoked
        self._cell = None


    def get_descriptor (self):
        """ returns the descriptor of this cell"""

        return self._descriptor
        
    
    def get_coloffset (self):
        """ returns the column offset of this cell"""

        return self._coloffset
        
    
    def get_rowoffset (self):
        """ returns the row offset of this cell"""

        return self._rowoffset

    def __str__ (self):
        '''provides a human readable representation of the contents of this intance'''

        if self._coloffset or self._rowoffset:
            output = self._descriptor + " + (" + str (self._coloffset) + ", " + str (self._rowoffset) + ")"
        else:
            output = self._descriptor

        # if this cell is already known 
        if self._cell:
            return self._cell + ": " + output

        # otherwise return a textual interpretation of the contents of this instance
        return output

    def execute (self, context):
        """compute the exact location of this cell: if a variable is used, it is
        resolved with the context. Additionally, if an offset is given, it is
        applied as well.

        A context is a dictionary of variable names to cell names

        """

        # is the descript a cell given explicitly? If so, use it directly,
        # otherwise, retrieve it from the context
        if re.match ("[a-zA-Z]+\d+", self._descriptor):
            self._cell = self._descriptor
        else:
            if self._descriptor in context:
                self._cell = context[self._descriptor]
            else:
                raise ValueError (" The descriptor {0} was not found in the context {1}".format (self._descriptor, context))

        # now, once the location is known, apply the offset
        self._cell = structs.add_columns (self._cell, self._coloffset)
        self._cell = structs.add_rows (self._cell, self._rowoffset)
        
        # and return the cell
        return self._cell
    
    
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
           given as a tuple of two instances of SPSCellReference. Commands are
           characterized by their type (either writing literals or the result of
           a query), and the string with either the string to literally insert
           or the query to execute. Commands can be identified by their name but
           they are not forced to be given a name

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
           cells. Importantly, literals can contain variables in the form
           $<text>.<text>.<text> which should be resolved within the given
           context of the registry where they are executed

           Even if a direction is given, it is ignored for literals

        '''

        # create an instance invoking the constructor of the base class
        super (SPSLiteral, self).__init__(name=name, crange=crange, ctype='literal', text=text)
        self._direction = direction
        
    def __str__ (self):
        '''provides a human readable representation of the contents of this intance'''

        if self._name:
            return "\tLiteral '{0}' with contents '{1}' in range {2} : {3}".format (self._name, self._text, self._range[0], self._range[1])
        return "\tExplicit literal with contents '{0}' in range {1} : {2}".format (self._text, self._range[0], self._range[1])

    def execute (self, data, context):
        '''executes this literal updating the contents of the given array and the
           current context. It returns two components, a dynamic array with the
           contents that should be modified in the spreadsheet and a dictionary
           with all modifications to do to the context where this literal has
           been executed.

           Importantly, literals acknowledge the substitution of variables
           according to the given context

        '''

        # first of all, compute the range of cells where this command should be
        # executed
        rnge = structs.Range ([self._range[0].execute (context), self._range[1].execute (context)])

        # now, perform all necessay substitutions. First, those where variables
        # appear along with an offset
        text = evaluate (r'[a-zA-Z_]+\.[a-zA-Z_]+\.[a-zA-Z_]+', context, self._text)
        
        # next, substitute the occurrence of all variables which do not come
        # with an offset
        text = substitute (r'[a-zA-Z_]+\.[a-zA-Z_]+\.[a-zA-Z_]+', context, text)
        
        # now, initialize the indices to the four corners of the region where this
        # literal is about to be executed
        (left, top) = (sys.maxsize, sys.maxsize)
        (bottom, right) = (0, 0)

        # for all cells in the given array
        for cell in rnge:

            # get the column and row of this cell
            (column, row) = structs.get_columnrow (cell)

            # and update the corners of this region
            left = min (structs.get_columnindex (column), left)
            right = max (structs.get_columnindex (column), right)
            top = min (row, top)
            bottom = max (row, bottom)

            # and now provide support to formulas by dragging the literal to be
            # inserted. Compute the offset from the beginning of this range of
            # this cell
            offset = structs.sub_cells (rnge._start, cell)
            extext = drag (offset, text)

            # insert the contents of this literal as a cell content qualified by
            # its type
            data[cell] = SPSCellContent (extext, get_type (extext))

        # update now the context only in case this is a named literal
        if self._name:
            prefix = "literal." + self._name +  "."

            # first, the four corners
            context [prefix + "nw"] = structs.get_columnname (left) + str (top)
            context [prefix + "ne"] = structs.get_columnname (right) + str (top)
            context [prefix + "sw"] = structs.get_columnname (left) + str (bottom)
            context [prefix + "se"] = structs.get_columnname (right) + str (bottom)

            # and now the mid points in the four sides
            context [prefix + "north"] = structs.get_columnname ((left + right) / 2) + str (top)
            context [prefix + "south"] = structs.get_columnname ((left + right) / 2) + str (bottom)
            context [prefix + "west"]  = structs.get_columnname (left) + str (int ((top+bottom) / 2))
            context [prefix + "east"]  = structs.get_columnname (right) + str (int ((top+bottom) / 2))

        # and return the contents created by the execution of this litral
        return (data, context)
    
        
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
            return "\tQuery '{0}' with contents '{1}' in range {2} : {3} with direction {4}".format (self._name, self._text, self._range[0], self._range[1], self._direction)
        return "\tQuery '{0}' with contents '{1}' in range {2} : {3}".format (self._name, self._text, self._range[0], self._range[1])

    def get_direction (self):
        '''return the direction of this command'''

        return self._direction

    def get_dbref (self):
        '''return the specific database to use when executing this query'''

        return self._dbref

    def execute (self, data, context, dbname=None):
        '''executes the result of this query by updating the contents of the given array
           using the given database (unless this query has been created wrt a
           specific database; in such a case, that specific database is used
           instead), and the current context.

           It returns two components, a dynamic array with the contents that
           should be modified in the spreadsheet and a dictionary with all
           modifications to do to the context where this literal has been
           executed.

           Note it is possible to provide no database as this query might
           contain a reference to the database to use which can not be overriden
           by any directive.

        '''

        # first of all, compute the range of cells where this command should be
        # executed
        rnge = structs.Range ([self._range[0].execute (context), self._range[1].execute (context)])
        
        # initialize the indices to the four corners of the region where this
        # query is about to be executed
        (left, top) = (sys.maxsize, sys.maxsize)
        (bottom, right) = (0, 0)
        
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

                # get the column and row of this cell
                (column, row) = structs.get_columnrow (cell)

                # and update the corners of this region
                left = min (structs.get_columnindex (column), left)
                right = max (structs.get_columnindex (column), right)
                top = min (row, top)
                bottom = max (row, bottom)

                # write the index-th value of this tuple in this cell
                data [cell] = value[i]

            # update the range by sliding it in the given direction
            if self._direction == 'down':
                rnge = rnge.add_rows (rnge.number_of_rows ())
            else:
                rnge = rnge.add_columns (rnge.number_of_columns ())

        # update now the context only in case this is a named literal
        prefix = "query." + self._name +  "."
        
        # first, the four corners
        context [prefix + "nw"] = structs.get_columnname (left) + str (top)
        context [prefix + "ne"] = structs.get_columnname (right) + str (top)
        context [prefix + "sw"] = structs.get_columnname (left) + str (bottom)
        context [prefix + "se"] = structs.get_columnname (right) + str (bottom)
        
        # and now the mid points in the four sides. Note that in case the cell
        # in the middle is an odd number, the largest integer below it is
        # selected
        context [prefix + "north"] = structs.get_columnname (math.floor ((left + right) / 2)) + str (top)
        context [prefix + "south"] = structs.get_columnname (math.floor ((left + right) / 2)) + str (bottom)
        context [prefix + "west"]  = structs.get_columnname (left) + str (int ((top+bottom) / 2))
        context [prefix + "east"]  = structs.get_columnname (right) + str (int ((top+bottom) / 2))

        # and return the new data
        return (data, context)
    
        
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
        '''when creating a registry either a command or none has to be given. Commands
           should be given as instances of SPSCommand (or any of its subtypes)

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

        # a registry keeps a context with different variables with the regions
        # filled by the queries and literals in it.
        context = dict ()
        
        # initialize a dynamic array to store all contents created by
        # the execution of all commands in this registry
        contents = DynamicArray ()

        # for all commands in this registry
        for command in self._registry:

            # add the contents created by the execution of this command
            if command.get_type () == 'literal':
                (contents, context) = command.execute (contents, context)
            else:
                (contents, context) = command.execute (contents, context, dbname)

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
        output += "\n Registry   :\n{0}".format (self._registry)

        return output

    def execute (self, dbname = None, spsname = None, sheetname = None, override=False):
        '''executes all commands in the registry of this spreadsheet. It returns a tuple
           with the name of the spreadsheet that should be updated and a dict
           with only one key, the name of the spreadsheet and a dynamic array
           with its contentss.

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

        # If no sheetname is computed then "Unnamed" is used by default
        if not sheetnameref:
            sheetnameref = "Unnamed"

        print (" Creating '{0}:{1}' ...".format (spsref, sheetnameref))
        
        # and now execute all commands in the current registry. The result is an
        # array of contents to insert into the spreadsheet
        contents = self._registry.execute (dbref)

        # and now, create a dictionary with the contents of this sheet
        sheet = dict ()
        sheet [sheetnameref] = contents.get_data ()

        # and return a tuple: first with the filename that should contain this
        # sheet; ssecond, its contents
        return (spsref, sheet)
        

# -----------------------------------------------------------------------------
# SPSBook
#
# A book consists of a list of spreadsheets
# -----------------------------------------------------------------------------
class SPSBook:
    """A book consists of a list of spreadsheets

    """

    def __init__ (self, sps = None):
        '''A table can be created empty but, if given, it is initialized with
           an instance of SPSSpreadsheet

        '''

        # init the book if a spreadsheet is given
        self._book = []
        if sps:
            self._book.append (sps)

        # also init the private counter used for iterating
        self._ith = 0        
    
    def __add__ (self, other):
        '''extends this book with all spreadsheets in a different table'''

        self._book += other._book
        return self
    
    def __iter__ (self):
        '''defines the simplest case for iterators'''
        
        return self

    def __next__ (self):
        '''returns the next spreadsheet in this book

        '''

        # if we did not reach the limit
        if self._ith < len (self._book):

            # return the current spreadsheet after incrementing the
            # private counter
            sps = self._book [self._ith]
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
        for sps in self._book:
            output += "{0}\n".format (sps)

        return output


    def write_to_pyexcel (self, filename, contents):
        '''use pyexcel to create a spreadsheet with the given filename and the specified
           contents. The contents consist of a dictionary where the keys are the
           sheetname and the value consists of a list of lists, each one
           containing the items in each row starting from row 1.

           The contents of each cell are specified as instances of
           SPSCellContent. 

           Rougly speaking, this method strips data and types from the instances
           of SPSCellContent

        '''

        # create a book for this spreadsheet 
        book = pyexcel.Book ()

        # process the contents
        pyexcel_bookdict = dict ()            # create a dict to store all sheets
        for key, data in contents.items ():
            pyexcel_contents = list ()        # data to write to this sheet
            for row in data:                  # for each row starting from 1
                irow = []                     # create a new list for this row
                for cell in row:              # and ach column in this row
                    if cell:                  # if there are contents, write'em
                        irow.append (cell.get_data ())
                    else:
                        irow.append (None)    # otherwise, leave them empty
                pyexcel_contents.append (irow)

            # and now add these contents to a new sheet as required by pyexcel
            # where the index is the sheetname and the contents are those just
            # processed
            pyexcel_bookdict [key] = pyexcel_contents

        print (pyexcel_bookdict)
            
        # write data to the spreadsheet
        book.bookdict = pyexcel_bookdict

        # and save its contents to this file
        book.save_as (filename)
        
    
    def execute (self, dbname = None, spsname = None, sheetname = None, override=False):
        '''executes all commands in the registry of all spreadsheets in this
           book effectively inserting data into the given
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

        # create a dictionary which should contain the books for each file that
        # should be generated
        files = dict ()
        
        # for all spreadsheets in this book
        for sps in self._book:

            # execute all commands in the registry of this specific
            # spreadsheet
            (filename, sheet) = sps.execute (dbname, spsname, sheetname, override)

            # if this is the first sheet generated in this spreadsheet
            if filename not in files:

                # then add this sheet to a new file
                files[filename] = sheet

            # otherwise
            else:

                # if a sheet already exists in this spreadsheet with the same
                # name
                if list(sheet.keys ())[0] in files[filename]:

                    raise ValueError (" The file '{0}' already contains a sheet named '{1}'".format (filename, list(sheet.keys ())[0]))

                # otherwise, add this sheet to this spreadsheet
                else:
                    
                    files[filename].update (sheet)

        # now, iterate over all files to generate
        for spreadsheet in files.keys ():

            # if this is an excel 2007 or xlsx file then use xlswriter
            if re.match (".*\.xlsx", spreadsheet):

                print (" Support for xlswriter not developed yet!")

            else:

                self.write_to_pyexcel (spreadsheet, files[spreadsheet])
                

            
    
# Local Variables:
# mode:python
# fill-column:80
# End:
