#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dbparser.py
# Description: A parser for the db language used to specify database tables
# -----------------------------------------------------------------------------
#
# Started on  <Tue Jul 24 15:18:45 2018 >
# -----------------------------------------------------------------------------
#
# Carlos Linares Lopez
# Login   <carlos.linares@uc3m.es>
#

"""
A parser for the db language used to specify database tables
"""

# imports
# -----------------------------------------------------------------------------
import re                               # match
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
class DBParser:
    """
    Class used to define the lex and grammar rules necessary for
    interpreting the db language used for specifying database tables
    """

    # reserved words
    reserved_words = {
        'using'     : 'USING',
        'exec'      : 'EXEC',
        'date'      : 'DATE',
        'datetime'  : 'DATETIME',
        'integer'   : 'INTEGER',
        'real'      : 'REAL',
        'text'      : 'TEXT',
        'None'      : 'NONE',
        'Warning'   : 'WARNING',
        'Error'     : 'ERROR'
        }

    # List of token names. This is always required
    tokens = (
        'DATETIMEEXP',
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
        ) + tuple(reserved_words.values())

    def __init__(self):
        """
        Constructor
        """

        # Build the lexer and parser
        self._lexer = lex.lex(module=self)
        self._parser = yacc.yacc(module=self, write_tables=0)

    # lex rules
    # -------------------------------------------------------------------------

    # Regular expression rules for simple tokens
    t_LCURBRACK = r'\{'
    t_RCURBRACK = r'\}'
    t_LPARENTHESIS = r'\('
    t_RPARENTHESIS = r'\)'
    t_SEMICOLON = r';'
    t_COLON = r':'
    t_COMMA = r','

    # datetimes are defined as three groups of digits separated by either
    # slashes or dashes along with the time given explicitly in the format
    # HH:MM:SS(.mmmmmm) where mmm are microseconds. Note that the first and last
    # group of the date are allowed to have up to four different digits, this is
    # illegal, clearly, but it allows the definition of dates where the year is
    # given either first or last
    def t_DATETIMEEXP(self, t):
        r'\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\s+\d{1,2}:\d{1,2}:\d{1,2}(\.\d{1,6})?'

        return t

    # dates are defined as three groups of digits separated by either slashes or
    # dashes. Note that the first and last group are allowed to have up to four
    # different digits, this is illegal, clearly, but it allows the definition
    # of dates where the year is given either first or last
    def t_DATEEXP(self, t):
        r'\d{1,4}[/-]\d{1,2}[/-]\d{1,4}'

        return t

    # Definition of both integer and real numbers
    def t_NUMBER(self, t):
        r'(([\+-]?\d*\.\d+)(E[\+-]?\d+)?|([\+-]?\d+E[\+-]?\d+))|[\+-]?\d+'

        # check whether this is a floating-point number
        if re.match(r'(([\+-]?\d*\.\d+)(E[\+-]?\d+)?|([\+-]?\d+E[\+-]?\d+))', t.value):
            t.value = float(t.value)

        # or an integer number
        elif re.match(r'[\+-]?\d+', t.value):
            t.value = int(t.value)

        return t

    # A regular expression for recognizing both single and doubled quoted
    # strings in a single line
    def t_STRING(self, t):
        r"""\"([^\\\n]|(\\.))*?\"|'([^\\\n]|(\\.))*?'"""

        return t

    # The following rule distinguishes automatically between reserved words and
    # identifiers. If a string is recognized as a reserved word, it is
    # returned. Otherwise, the token 'ID' is returned
    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_\d]*'

        t.type = self.reserved_words.get(t.value, 'ID')   # Check for reserved words
        return t

    # Definition of cells as an alpha character and a number
    def t_CELL(self, t):
        r'\$[a-zA-Z]+\d+'

        return t

    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'

        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs)
    t_ignore = ' \t'

    # Rule to skip comments
    def t_COMMENT(self, t):
        r'\#.*'

    # Error handling rule
    def t_error(self, t):

        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # grammar rules
    # -------------------------------------------------------------------------

    # definition of legal statements
    # -----------------------------------------------------------------------------

    # a valid db specification consists of tables
    def p_definitions(self, p):
        '''definitions : expression
                       | expression definitions'''

        # note that in the following both tables and sql statements are created
        # the same way. This is because DBDatabase accepts both definitions
        if len(p) == 2:
            p[0] = dbstructs.DBDatabase([p[1]])
        elif len(p) == 3:
            p[0] = dbstructs.DBDatabase([p[1]]) + p[2]

    # expressions can be either tables or SQL statements
    def p_expression(self, p):
        '''expression : sqlstatement
                      | table'''

        # just distinguish among them and return an instance of the appropriate
        # type
        p[0] = p[1]


    # definition of SQL statements
    # -----------------------------------------------------------------------------
    def p_sqlstatements(self, p):
        '''sqlstatement : EXEC STRING'''

        # create the corresponding executable SQL statement ---removing the
        # double quotes
        p[0] = dbstructs.DBSQLStatement(p[2][1:-1])


    # definition of data tables
    # -----------------------------------------------------------------------------
    def p_table(self, p):
        '''table : ID LCURBRACK columns RCURBRACK
                 | ID USING STRING LCURBRACK columns RCURBRACK
                 | ID USING STRING COLON STRING LCURBRACK columns RCURBRACK'''

        if len(p) == 5:
            p[0] = dbstructs.DBTable(p[1], None, None, p[3])
        elif len(p) == 7:

            # remove the double quotes in the spreadsheet name
            p[0] = dbstructs.DBTable(p[1], p[3][1:-1], None, p[5])
        else:

            # remove the double quotes in the spreadsheet name and the sheetname
            p[0] = dbstructs.DBTable(p[1], p[3][1:-1], p[5][1:-1], p[7])

    def p_columns(self, p):
        '''columns : column
                   | column columns'''

        if len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 3:
            p[0] = [p[1]] + p[2]

    def p_column(self, p):
        '''column : ID content SEMICOLON
                  | ID content type SEMICOLON
                  | ID content action SEMICOLON
                  | ID content type action SEMICOLON'''

        if len(p) == 4:
            p[0] = dbstructs.DBColumn(p[1], p[2], None, None)
        if len(p) == 5:

            # if the type was given but not an action
            if p[3] in ["integer", "real", "text", "datetime", "date"]:
                p[0] = dbstructs.DBColumn(p[1], p[2], p[3], dbstructs.DBAction('None'))

            # otherwise, if an action is given (but not its type)
            else:
                p[0] = dbstructs.DBColumn(p[1], p[2], None, p[3])
        if len(p) == 6:
            p[0] = dbstructs.DBColumn(p[1], p[2], p[3], p[4])

    # the definition of columns accepts data coming either from the spreadsheet
    # (as a sequence of regions), or given explicitly
    def p_content(self, p):
        '''content : rangelist
                   | explicit'''

        p[0] = p[1]

    # data explicitly given is defined literally, as much as when defining
    # default values. The difference though is that data has to go encapsulated
    # in a specific type for explicit data
    def p_explicit(self, p):
        '''explicit : default'''

        p[0] = dbstructs.DBExplicit(p[1])

    def p_rangelist(self, p):
        '''rangelist : range
                     | range COMMA rangelist'''

        if len(p) == 2:
            p[0] = dbstructs.DBRanges([p[1]])
        else:
            p[0] = dbstructs.DBRanges([p[1]]) + p[3]

    def p_range(self, p):
        '''range : CELL
                 | CELL COLON CELL'''

        # return this range removing first the heading '$'
        if len(p) == 2:
            p[0] = structs.Range([p[1][1:], p[1][1:]])
        else:
            p[0] = structs.Range([p[1][1:], p[3][1:]])

    # note that the only allowed types are numbers (either integers or
    # floating-point numbers), strings and time specifications
    def p_type(self, p):
        '''type : DATETIME
                | DATE
                | INTEGER
                | REAL
                | TEXT'''

        p[0] = p[1]

    def p_action(self, p):
        '''action : NONE
                  | WARNING
                  | ERROR
                  | default
                  | NONE LPARENTHESIS default RPARENTHESIS
                  | WARNING LPARENTHESIS default RPARENTHESIS'''

        if len(p) == 2:

            # if an action is given without a default value, then create it with
            # "None" action
            if p[1] == 'None' or p[1] == 'Warning' or p[1] == 'Error':
                p[0] = dbstructs.DBAction(p[1], None)
            else:

                # if only a default value is given, then consider the action to
                # be "None"
                p[0] = dbstructs.DBAction('None', p[1])
        else:

            # if, on the other hand, an action is given with a default value,
            # then create an action with both fields
            p[0] = dbstructs.DBAction(p[1], p[3])

    # a default value can be given as a number (either integer or real), a
    # datetime, a date, or a string
    def p_default(self, p):
        '''default : DATETIMEEXP
                   | DATEEXP
                   | NUMBER
                   | STRING'''

        p[0] = p[1]

    # error handling
    # -----------------------------------------------------------------------------
    # Error rule for syntax errors
    def p_error(self, p):
        print(" Syntax error in line {0} near '{1}': unexpected token {2} found".format(p.lineno, p.value, p.type))
        print()
        sys.exit()


# -----------------------------------------------------------------------------
# VerbatimDBParser
#
# Class used to process a verbatim string
# -----------------------------------------------------------------------------
class VerbatimDBParser(DBParser):
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
class InteractiveDBParser(DBParser):
    """
    Class used to run the parser in interactive mode
    """

    def run(self):
        """
        Enter a never-ending loop processing input as it comes
        """

        while True:
            try:
                stream = input('db> ')
            except EOFError:
                break
            if not stream:
                continue
            return self._parser.parse(stream, lexer=self._lexer)


# -----------------------------------------------------------------------------
# FileDBParser
#
# Class used to parse the contents of the given file
# -----------------------------------------------------------------------------
class FileDBParser(DBParser):
    """
    Class used to parse the contents of the given file
    """

    def run(self, filename):
        """
        Just read the contents of the given file and process them
        """

        with open(filename, encoding="utf-8") as fstream:

            return self._parser.parse(fstream.read(), lexer=self._lexer)



# Local Variables:
# mode:python
# fill-column:80
# End:
