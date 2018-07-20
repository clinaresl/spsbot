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


# classes
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# SPSCommand
#
# Definition of a basic command
# -----------------------------------------------------------------------------
class SPSCommand:
    """Definition of a basic command

    """

    def __init__ (self, crange, ctype, text):

        '''a command consists of writing data into the spreadsheet in the
           given range. Commands are characterized by their type
           (either writing literals or the result of a query), and the
           string with either the string to literally insert or the
           query to execute. This is the base class of all type of
           commands

           The range should be given as an instance of Range

        '''

        self._range, self._type, self._text = crange, ctype, text

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

    def __init__ (self, crange, text, direction=None):
        '''a literal consists of inserting the given text in an arbitrary
number of cells. In case a direction is given the command replicates
the literal in the given direction

        '''

        # create an instance invoking the constructor of the base class
        super (SPSLiteral, self).__init__(crange=crange, ctype='literal', text=text)
        self._direction = direction
        
    def __str__ (self):
        '''provides a human readable representation of the contents of this intance'''

        if self._direction:
            return "Literal '{0}' in range {1} with direction".format (self._text, self._range, self._direction)
        return "Literal '{0}' in range {1}".format (self._text, self._range)

        
# -----------------------------------------------------------------------------
# SPSQuery
#
# Definition of a command which consists of inserting the result of a
# sql query
# -----------------------------------------------------------------------------
class SPSQuery (SPSCommand):
    """Definition of a command which consists of inserting the result of a
       sql query

    """

    def __init__ (self, crange, text, direction=None):
        '''a query consists of inserting the result of a sql query in an
arbitrary number of cells. As there might be an arbitrary number of
results, all tuples are inserted in the given direction. However, it is assumed by default that the result of the query consists of a single tuple and thus, there is no direction

        '''

        # create an instance invoking the constructor of the base class
        super (SPSQuery, self).__init__(crange=crange, ctype='query', text=text)
        self._direction = direction
        
    
    def __str__ (self):
        '''provides a human readable representation of the contents of this intance'''

        if self._direction:
            return "Query '{0}' in range {1} with direction {2}".format (self._text, self._range, self._direction)
        return "Query '{0}' in range {1}".format (self._text, self._range)

    def get_direction (self):
        '''return the direction of this command'''

        return self._direction


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

    
    
# Local Variables:
# mode:python
# fill-column:80
# End:
