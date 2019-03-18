#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dbparser.py
# Description: A parser for the db language used to specify database tables
# -----------------------------------------------------------------------------
# Login   <clinares@atlas>
#

"""
A parser for the db language used to specify database tables
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
import dbstructs

# classes
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# DBParser
#
# Class used to define the lex and grammar rules necessary for
# interpreting the db language used for specifying database tables
# -----------------------------------------------------------------------------
class DBParser :
    """
    Class used to define the lex and grammar rules necessary for
    interpreting the db language used for specifying database tables
    """

    # reserved words
    reserved_words = {
        'using'     : 'USING',
        'date'      : 'DATE',
        'integer'   : 'INTEGER',
        'real'      : 'REAL',
        'text'      : 'TEXT',
        'None'      : 'NONE',
        'Warning'   : 'WARNING',
        'Error'     : 'ERROR'
        }

    # List of token names. This is always required
    tokens = (
        'DATEEXP',
        'NUMBER',
        'STRING',
        'LCURBRACK',
        'RCURBRACK',
        'LPARENTHESIS',
        'RPARENTHESIS',
        'SEMICOLON',
        'COLON',
        'COMMA',
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

    # dates are defined as three groups of digits separated by either slashes or
    # dashes. Note that the first and last group are allowed to have up to four
    # different digits, this is illegal, clearly, but it allows the definition
    # of dates where the year is given either first or last
    def t_DATEEXP (self, t):
        r'\d{1,4}[/-]\d{1,2}[/-]\d{1,4}'
    
    # Definition of both integer and real numbers
    def t_NUMBER(self, t):
        r'(([\+-]?\d*\.\d+)(E[\+-]?\d+)?|([\+-]?\d+E[\+-]?\d+))|[\+-]?\d+'

        # check whether this is a floating-point number
        if re.match (r'(([\+-]?\d*\.\d+)(E[\+-]?\d+)?|([\+-]?\d+E[\+-]?\d+))', t.value):
            t.value = float (t.value)
            
        # or an integer number
        elif re.match (r'[\+-]?\d+', t.value):
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

    # a valid db specification consists of tables
    def p_definitions (self, p):
        '''definitions : table
                       | table definitions'''

        if len (p) == 2:
            p[0] = dbstructs.DBDatabase ([p[1]])
        elif len (p) == 3:
            p[0] = dbstructs.DBDatabase ([p[1]]) + p[2]

    # definition of data tables
    # -----------------------------------------------------------------------------
    def p_table (self, p):
        '''table : ID LCURBRACK columns RCURBRACK
                 | ID USING STRING LCURBRACK columns RCURBRACK
                 | ID USING STRING COLON STRING LCURBRACK columns RCURBRACK'''

        if len (p) == 5:
            p[0] = dbstructs.DBTable (p[1], None, None, p[3])
        elif len (p) == 7:

            # remove the double quotes in the spreadsheet name
            p[0] = dbstructs.DBTable (p[1], p[3][1:-1], None, p[5])
        else:

            # remove the double quotes in the spreadsheet name and the sheetname
            p[0] = dbstructs.DBTable (p[1], p[3][1:-1], p[5][1:-1], p[7])
        
    def p_columns (self, p):
        '''columns : column
                   | column columns'''

        if len (p) == 2:
            p[0] = [p[1]]
        elif len (p) == 3:
            p[0] = [p[1]] + p[2]

    def p_column (self, p):
        '''column : ID rangelist SEMICOLON
                  | ID rangelist type SEMICOLON
                  | ID rangelist action SEMICOLON
                  | ID rangelist type action SEMICOLON'''

        if len (p) == 4:
            p[0] = dbstructs.DBColumn (p[1], p[2], None, None)
        if len (p) == 5:

            # if the type was given but not an action
            if p[3] in ["integer", "real", "text", "date"]:
                p[0] = dbstructs.DBColumn (p[1], p[2], p[3], dbstructs.DBAction ('None'))

            # otherwise, if an action is given (but not its type)
            else:
                p[0] = dbstructs.DBColumn (p[1], p[2], None, p[3])
        if len (p) == 6:
            p[0] = dbstructs.DBColumn (p[1], p[2], p[3], p[4])

    def p_rangelist (self, p):
        '''rangelist : range
                     | range COMMA rangelist'''

        if len (p) == 2:
            p[0] = dbstructs.DBRanges ([p[1]])
        else:
            p[0] = dbstructs.DBRanges ([p[1]]) + p[3]
            
    def p_range (self, p):
        '''range : CELL
                 | CELL COLON CELL'''

        # return this range removing first the heading '$'
        if len (p) == 2:
            p[0] = structs.Range ([p[1][1:], p[1][1:]])
        else:
            p[0] = structs.Range ([p[1][1:], p[3][1:]])
            
    def p_type (self, p):
        '''type : DATE
                | INTEGER
                | REAL
                | TEXT'''

        p[0] = p[1]

    def p_action (self, p):
        '''action : NONE
                  | WARNING
                  | ERROR
                  | default
                  | NONE LPARENTHESIS default RPARENTHESIS
                  | WARNING LPARENTHESIS default RPARENTHESIS'''

        if len (p) == 2:

            # if an action is given without a default value, then create it with
            # "None" action
            if p[1]=='None' or p[1]=='Warning' or p[1]=='Error':
                p[0] = dbstructs.DBAction (p[1], None)
            else:

                # if only a default value is given, then consider the action to
                # be "None"
                p[0] = dbstructs.DBAction ('None', p[1])
        else:

            # if, on the other hand, an action is given with a default value,
            # then create an action with both fields
            p[0] = dbstructs.DBAction (p[1], p[3])

    # a default value can be given as a number (either integer or real), a date,
    # or a string
    def p_default (self, p):
        '''default : DATEEXP
                   | NUMBER
                   | STRING'''

        p[0] = p[1]

    # error handling
    # -----------------------------------------------------------------------------
    # Error rule for syntax errors
    def p_error(self, p):
        print("Syntax error while processing the database specification file!")
        print ()
        sys.exit ()
    

# -----------------------------------------------------------------------------
# VerbatimDBParser
#
# Class used to process a verbatim string
# -----------------------------------------------------------------------------
class VerbatimDBParser (DBParser):
    """
    Class used to process a verbatim string
    """

    def run(self, data):
        """
        Just parse the given string
        """

        self._tables = self._parser.parse(data, lexer=self._lexer)


# -----------------------------------------------------------------------------
# InteractiveDBParser
#
# Class used to run the parser in interactive mode
# -----------------------------------------------------------------------------
class InteractiveDBParser (DBParser):
    """
    Class used to run the parser in interactive mode
    """

    def run(self):
        """
        Enter a never-ending loop processing input as it comes
        """

        while True:
            try:
                s = input('db> ')
            except EOFError:
                break
            if not s: continue
            return self._parser.parse(s, lexer=self._lexer)


# -----------------------------------------------------------------------------
# FileDBParser
#
# Class used to parse the contents of the given file
# -----------------------------------------------------------------------------
class FileDBParser (DBParser):
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
