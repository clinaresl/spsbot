#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# spsparser.py
# Description: A parser for the sps language used to specify the
# contents of spreadsheets
# -----------------------------------------------------------------------------
#
# Started on  <Wed Jul 11 20:29:55 2018 >
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
A parser for the sps language used to specify the contents of spreadsheets
"""

# globals
# -----------------------------------------------------------------------------
__version__  = '1.0'


# imports
# -----------------------------------------------------------------------------
import re                               # match
import string                           # split
import sys                              # exit

import ply.lex as lex
import ply.yacc as yacc

import structs
import spsstructs

# classes
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# SPSParser
#
# Class used to define the lex and grammar rules necessary for
# interpreting the sps language used for specifying the contents of
# spreadsheets
# -----------------------------------------------------------------------------
class SPSParser :
    """Class used to define the lex and grammar rules necessary for
    interpreting the sps language used for specifying the contents of
    spreadsheets

    """

    # reserved words
    reserved_words = {
        'literal'   : 'LITERAL',
        'query'     : 'QUERY',
        'using'     : 'USING',
        'right'     : 'RIGHT',
        'down'      : 'DOWN'
        }

    # List of token names. This is always required
    tokens = (
        'NUMBER',
        'STRING',
        'LCURBRACK',
        'RCURBRACK',
        'LPARENTHESIS',
        'RPARENTHESIS',
        'SEMICOLON',
        'COLON',
        'COMMA',
        'DOT',
        'ID',
        'CELL'
        ) + tuple(reserved_words.values ())

    def __init__ (self):
        """
        Constructor
        """

        # Build the lexer and parser
        self._lexer = lex.lex(module=self)
        self._parser = yacc.yacc(module=self,write_tables=0)

        # create also the symbol tables
        self._query_table = dict ()
        self._literal_table = dict ()

    # lex rules
    # -------------------------------------------------------------------------

    # Regular expression rules for simple tokens
    t_LCURBRACK  = r'\{'
    t_RCURBRACK  = r'\}'
    t_LPARENTHESIS = r'\('
    t_RPARENTHESIS = r'\)'
    t_SEMICOLON  = r';'
    t_COLON      = r':'
    t_COMMA      = r','
    t_DOT        = r'\.'

    # Definition of both integer and real numbers
    def t_NUMBER(self, t):
        r'[\+-]?\d+'

        t.value = int (t.value)
        return t

    # A regular expression for recognizing both single and doubled quoted
    # strings in a single line
    def t_STRING (self, t):
        r"""\"([^\\\n]|(\\.))*?\"|'([^\\\n]|(\\.))*?'"""

        return t

    # The following rule distinguishes automatically between reserved words and
    # identifiers. If a string is recognized as a reserved word, it is
    # returned. Otherwise, the token 'ID' is returned
    def t_ID (self, t):
        r'[a-zA-Z_][a-zA-Z_\d]*'

        t.type = self.reserved_words.get(t.value,'ID')   # Check for reserved words
        return t

    # Definition of cells as an alpha character and a number
    def t_CELL (self, t):
        r'\$[a-zA-Z]+\d+'

        return t
    
    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'

        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs)
    t_ignore  = ' \t'

    # Rule to skip comments
    def t_COMMENT (self, t):
        r'\#.*'

        pass                                     # No return value. Token discarded

    # Error handling rule
    def t_error(self, t):

        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # grammar rules
    # -------------------------------------------------------------------------

    # definition of legal statements
    # -----------------------------------------------------------------------------

    # a valid sps specification consists of an arbitrary (and even null) number
    # of literal/query declarations and spreadsheets. Declarations can be
    # interspersed with the spreadsheets for improving legibility.
    def p_definitions (self, p):
        '''definitions : declaration
                       | spreadsheet
                       | declaration definitions
                       | spreadsheet definitions'''

        if isinstance (p[1], spsstructs.SPSSpreadsheet):

            if len (p) == 2:
                p[0] = spsstructs.SPSDeck (p[1])
            else:
                p[0] = spsstructs.SPSDeck (p[1]) + p[2]

        else:
            
            if len (p) == 3:
                p[0] = p[2]
                

    # the sps specification language accepts the declaration of both literals
    # and queries.
    def p_declaration (self, p):
        '''declaration : literaldec
                       | querydec'''

        pass

    # the declaration of a literal consists just of the assignment of a string
    # to an identifier
    def p_literaldec (self, p):
        '''literaldec : LITERAL ID STRING'''

        # add this definition to the symbol table of literals only in case it
        # does not exist
        if p[3] in self._literal_table:

            print (" Fatal Error - Conflicting definitions for literal '{0}'".format (p[3]))
            sys.exit (0)
            
        self._literal_table [p[2]] = p[3]

    # likewise, the declaration of a query consists of the assignment of a query
    # to an identifier
    def p_querydec (self, p):
        '''querydec : QUERY ID STRING'''
    
        # add this definition to the symbol table of queries only in case it
        # does not exist
        if p[3] in self._query_table:

            print (" Fatal Error - Conflicting definitions for query '{0}'".format (p[3]))
            sys.exit (0)
            
        self._query_table [p[2]] = p[3]

    # the definition of a spreadsheet consists just of a name of the spreadsheet
    # to create, the sheet name to use and the database to use for extracting
    # data and the commands to write data into the spreadsheet between curly
    # brackets
    def p_spreadsheet (self, p):
        '''spreadsheet : LCURBRACK commands RCURBRACK'''

        p[0] = spsstructs.SPSSpreadsheet (p[2])
                
    def p_commands (self, p):
        '''commands : command
                    | command commands
        '''

        if len (p) == 2:
            p[0] = spsstructs.SPSRegistry (p[1])
        if len (p) == 3:
            p[0] = spsstructs.SPSRegistry (p[1]) + p[2]
        
    # there are mainly two types of commands: either for writing literals or
    # queries. By default, literals are inserted into a single cell, whereas
    # queries are given wrt a region. However, it is also possible to insert the
    # result of a query in a cell and also to replicate a string in all cells of
    # a region.
    def p_command (self, p):
        '''command : CELL content
                   | CELL COLON CELL direction content'''

        if len (p) == 3:
            
            if p[2][0] == 'Literal':
                p[0] = spsstructs.SPSLiteral (structs.Range ([p[1][1:],p[1][1:]]), p[2][1])
            if p[2][0] == 'Query':
                p[0] = spsstructs.SPSQuery (structs.Range ([p[1][1:],p[1][1:]]), p[2][1])
                
        if len (p) == 6:
            
            if p[5][0] == 'Literal':
                p[0] = spsstructs.SPSLiteral (structs.Range ([p[1][1:],p[3][1:]]), p[5][1], p[4])
            if p[5][0] == 'Query':
                p[0] = spsstructs.SPSQuery (structs.Range ([p[1][1:],p[3][1:]]), p[5][1], p[4])

    # contents can be either strings, literals or queries
    def p_content (self, p):
        '''content : STRING SEMICOLON
                   | LITERAL DOT ID SEMICOLON
                   | QUERY DOT ID SEMICOLON'''

        # this grammar rule returns a tuple with the type of content (either a
        # literal or a query), and its value. If literal/query declarations were
        # used, they are substituted here
        if len (p) == 3:
            p [0] = ('Literal', p[1])
        if len (p) == 5:

            if p[1] == 'literal':

                if p[3] not in self._literal_table:
                    print(" Fatal Error - Unknown literal '{0}'".format (p[3]))
                    sys.exit (0)
                
                p[0] = ('Literal', self._literal_table [p[3]])
            else:

                if p[3] not in self._query_table:
                    print(" Fatal Error - Unknown query '{0}'".format (p[3]))
                    sys.exit (0)
                
                p[0] = ('Query', self._query_table [p[3]])
        

    # in case a command is given wrt a region, its contents can be replicated
    # either to the right or downwards
    def p_direction (self, p):
        '''direction : RIGHT
                     | DOWN'''

        p [0] = p[1]
            
    
# -----------------------------------------------------------------------------
# InteractiveSPSParser
#
# Class used to run the parser in interactive mode
# -----------------------------------------------------------------------------
class InteractiveSPSParser (SPSParser):
    """
    Class used to run the parser in interactive mode
    """

    def run(self):
        """
        Enter a never-ending loop processing input as it comes
        """

        while True:
            try:
                s = input('sps> ')
            except EOFError:
                break
            if not s: continue
            return self._parser.parse(s, lexer=self._lexer)


# -----------------------------------------------------------------------------
# FileSPSParser
#
# Class used to parse the contents of the given file
# -----------------------------------------------------------------------------
class FileSPSParser (SPSParser):
    """
    Class used to parse the contents of the given file
    """

    def run(self, filename):
        """
        Just read the contents of the given file and process them
        """

        with open (filename, encoding="utf-8") as f:

            return self._parser.parse (f.read (), lexer=self._lexer)





# Local Variables:
# mode:python
# fill-column:80
# End:
