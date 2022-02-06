#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# spsparser.py
# Description: A parser for the sps language used to specify the
# contents of spreadsheets
# -----------------------------------------------------------------------------
#
# Started on  <Wed Jul 11 20:29:55 2018 >
# -----------------------------------------------------------------------------
#
# Carlos Linares Lopez
# Login   <carlos.linares@uc3m.es>
#

"""A parser for the sps language used to specify the contents of spreadsheets
from information in a database

"""

# imports
# -----------------------------------------------------------------------------
import datetime
import re                               # match
import sys                              # exit

import ply.lex as lex
import ply.yacc as yacc

from . import spsstructs
from . import utils

# globals
# -----------------------------------------------------------------------------
LOGGER = utils.LOGGER

# -- errors
ERROR_ILLEGAL_CHAR = "Illegal character '%s'"
ERROR_CONFLICT_LITERALS = "Conflicting definitions for literal '{0}'"
ERROR_CONFLICT_QUERIES = "Conflicting definitions for query '{0}'"
ERROR_UNKNOWN_LITERAL = "Unknown literal '{0}'"
ERROR_UNKNOWN_QUERY = "Unknown query '{0}'"
ERROR_SYNTAX_ERROR = "Syntax error in line {0} near '{1}': unexpected token {2} found"

# classes
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# SPSParser
#
# Class used to define the lex and grammar rules necessary for
# interpreting the sps language used for specifying the contents of
# spreadsheets
# -----------------------------------------------------------------------------
class SPSParser:
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
        'DATEEXP',
        'DATETIMEEXP',
        'REAL',
        'NUMBER',
        'STRING',
        'LCURBRACK',
        'RCURBRACK',
        'LPARENTHESIS',
        'RPARENTHESIS',
        'LSQUAREBRACKET',
        'RSQUAREBRACKET',
        'SEMICOLON',
        'COLON',
        'COMMA',
        'PLUS',
        'DOT',
        'ID',
        'CELL',
        'VARIABLE'
        ) + tuple(reserved_words.values())

    def __init__(self):
        """
        Constructor
        """

        # Build the lexer and parser
        self._lexer = lex.lex(module=self)
        self._parser = yacc.yacc(module=self, write_tables=0)

        # create also the symbol tables
        self._query_table = dict()
        self._literal_table = dict()

        # and the table for storing specific databases to use when defining
        # queries
        self._query_db = dict()

    # lex rules
    # -------------------------------------------------------------------------

    # Regular expression rules for simple tokens
    t_LCURBRACK = r'\{'
    t_RCURBRACK = r'\}'
    t_LPARENTHESIS = r'\('
    t_RPARENTHESIS = r'\)'
    t_LSQUAREBRACKET = r'\['
    t_RSQUAREBRACKET = r'\]'
    t_SEMICOLON = r';'
    t_COLON = r':'
    t_PLUS = r'\+'
    t_COMMA = r','
    t_DOT = r'\.'

    # datetimes are defined as three groups of digits separated by either
    # slashes or dashes along with the time given explicitly in the format
    # HH:MM:SS(.mmmmmm) where mmm are microseconds or, alternatively, by using
    # the keyword datetime.now. Note that the first and last group of the date
    # are allowed to have up to four different digits, this is illegal, clearly,
    # but it allows the definition of dates where the year is given either first
    # or last
    def t_DATETIMEEXP(self, t):
        r'\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\s+\d{1,2}:\d{1,2}:\d{1,2}(\.\d{1,6})?|datetime\.now'

        # is it one of the forms *.now?
        if re.match(r'datetime\.now', str(t.value)):
            t.value = datetime.datetime.now()

        # otherwise, cast the string to a datetime
        else:
            t.value = spsstructs.string_to_datetime(t.value)

        return t

    # dates are defined as three groups of digits separated by either slashes or
    # dashes or, alternatively, by using the keyword date.now. Note that the
    # first and last group are allowed to have up to four different digits, this
    # is illegal, clearly, but it allows the definition of dates where the year
    # is given either first or last
    def t_DATEEXP(self, t):
        r'\d{1,4}[/-]\d{1,2}[/-]\d{1,4}|date\.now'

        # is it one of the forms *.now?
        if re.match(r'date\.now', str(t.value)):
            t.value = datetime.date.today()

        # check if the format used was YYYY, mm, dd with either dashes or
        # slashes
        else:
            t.value = spsstructs.string_to_date(t.value)

        return t

    # Definitions of real numbers which intentionally do not match integer
    # numbers to avoid confussions with t_NUMBER. Note, in addition, that this
    # token precedes the NUMBER
    def t_REAL(self, t):
        r'[-+]?\d+(\.\d+|[.]?\d*[eE][-+]?\d+)'

        t.value = float(t.value)
        return t

    # Definition of numbers
    def t_NUMBER(self, t):
        r'[\+-]?\d+'

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

    # Definition of variables as three groups of alpha characters separated by
    # dots and preceded by a dollar sign. Note that the second group can contain
    # digits as well
    def t_VARIABLE(self, t):
        r'\$[a-zA-Z_]+\.[a-zA-Z_][a-zA-Z_\d]*\.[a-zA-Z_]+'

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

        # No return value. Token discarded


    # Error handling rule
    def t_error(self, t):

        LOGGER.error(ERROR_ILLEGAL_CHAR % t.value[0])
        t.lexer.skip(1)

    # grammar rules
    # -------------------------------------------------------------------------

    # definition of legal statements
    # -----------------------------------------------------------------------------

    # a valid sps specification consists of an arbitrary (and even null) number
    # of literal/query declarations and spreadsheets. Declarations can be
    # interspersed with the spreadsheets for improving legibility.
    def p_definitions(self, p):
        '''definitions : declaration
                       | spreadsheet
                       | declaration definitions
                       | spreadsheet definitions'''

        # declarations are processed directly by the parser, so that parsing
        # this grammar rule involves returning only information of the
        # spreadsheets
        if isinstance(p[1], spsstructs.SPSSpreadsheet):

            if len(p) == 2:
                p[0] = spsstructs.SPSBook(p[1])
            else:
                p[0] = spsstructs.SPSBook(p[1]) + p[2]

        else:

            # if the definition of spreadsheets is preceded of declarations,
            # make sure to returning all spreadsheets coming hereafter
            if len(p) == 3:
                p[0] = p[2]

    # the sps specification language accepts the declaration of both literals
    # and queries.
    def p_declaration(self, p):
        '''declaration : literaldec
                       | querydec'''

        # Nothing to be done, declarations do not generate structtures and they
        # are used as an intermediate rule


    # the declaration of a literal consists just of the assignment of an
    # instance of the basic types to an identifier
    def p_literaldec(self, p):
        '''literaldec : LITERAL ID DATETIMEEXP
                      | LITERAL ID DATEEXP
                      | LITERAL ID REAL
                      | LITERAL ID NUMBER
                      | LITERAL ID STRING'''

        # first, make sure this literal was not previously defined
        if p[2] in self._literal_table:

            LOGGER.error(ERROR_CONFLICT_LITERALS.format(p[2]))

        # otherwise, store it in way or another depending upon the type of
        # literal
        else:

            # if the literal is (either) a real or integer number then store it as
            # is
            # in case it is a string, then remove the quotes
            if isinstance(p[3], str):
                self._literal_table[p[2]] = p[3][1:-1]

            else:
                # in any other case (integer, real, datetime or date) just store
                # it as given
                self._literal_table[p[2]] = p[3]

    # likewise, the declaration of a query consists of the assignment of a query
    # to an identifier
    def p_querydec(self, p):
        '''querydec : QUERY ID STRING
                    | QUERY ID STRING USING STRING'''

        # add this definition to the symbol table of queries only in case it
        # does not exist
        if p[3] in self._query_table:

            LOGGER.error(ERROR_CONFLICT_QUERIES.format(p[3]))
            sys.exit(0)

        self._query_table[p[2]] = p[3]

        # in case a specific database has been given, then store it in a
        # different dict
        self._query_db[p[2]] = p[5][1:-1] if len(p) == 6 else None

    # the definition of a spreadsheet consists just of a name of the spreadsheet
    # to create, the sheet name to use and the database to use for extracting
    # data and the commands to write data into the spreadsheet between curly
    # brackets
    def p_spreadsheet(self, p):
        '''spreadsheet : LCURBRACK commands RCURBRACK
                       | header LCURBRACK commands RCURBRACK'''

        if len(p) == 4:
            p[0] = spsstructs.SPSSpreadsheet(p[2])
        else:
            p[0] = spsstructs.SPSSpreadsheet(p[3], p[1][0], p[1][1], p[1][2])

    # headers are optional and they can specify a spreadsheet, a sheet name
    # and/or a database to use for executing the queries specified here. Thus,
    # the first and second string refer to the spreadsheet location and sheet
    # name; if "using" is given, a database can be specified
    def p_header(self, p):
        '''header : filespec
                  | filespec USING STRING
        '''

        if len(p) == 2:
            p[0] = (p[1][0], p[1][1], None)
        else:
            p[0] = (p[1][0], p[1][1], p[3][1:-1])

    # a file specification serves to indicate the file that should be used for
    # generating the spreadsheet and a sheet name. Note that these are purely
    # optional. Indeed, ":" is a shortcut for ' "" : "" '
    def p_filespec(self, p):
        '''filespec : STRING COLON STRING
                    | STRING COLON
                    | COLON STRING
                    | COLON'''

        if len(p) == 4:
            p[0] = (p[1][1:-1], p[3][1:-1])
        if len(p) == 3:

            if p[1] == self.t_COLON:
                p[0] = (None, p[2][1:-1])
            else:
                p[0] = (p[1][1:-1], None)
        if len(p) == 2:
            p[0] = (None, None)

    def p_commands(self, p):
        '''commands : command
                    | command commands
        '''

        if len(p) == 2:
            p[0] = spsstructs.SPSRegistry(p[1])
        if len(p) == 3:
            p[0] = spsstructs.SPSRegistry(p[1]) + p[2]

    # there are mainly two types of commands: either for writing literals or
    # queries. By default, literals are inserted into a single cell, whereas
    # queries are given wrt a region. However, it is also possible to insert the
    # result of a query in a cell and also to replicate a string in all cells of
    # a region.
    def p_command(self, p):
        '''command : celldec content
                   | celldec attributes content
                   | celldec COLON celldec direction content
                   | celldec COLON celldec attributes direction content'''

        if len(p) == 3:

            if p[2][0] == 'Literal':
                p[0] = spsstructs.SPSLiteral(p[2][1], (p[1], p[1]),
                                             spsstructs.SPSCellContent(p[2][2], p[2][3]))
            if p[2][0] == 'Query':
                p[0] = spsstructs.SPSQuery(p[2][1], (p[1], p[1]),
                                           spsstructs.SPSCellContent(p[2][2], p[2][3]),
                                           p[2][4])

        if len(p) == 4:

            if p[3][0] == 'Literal':
                p[0] = spsstructs.SPSLiteral(p[3][1], (p[1], p[1]),
                                             spsstructs.SPSCellContent(p[3][2], p[3][3], p[2]))
            if p[3][0] == 'Query':
                p[0] = spsstructs.SPSQuery(p[3][1], (p[1], p[1]),
                                           spsstructs.SPSCellContent(p[3][2], p[3][3], p[2]),
                                           p[3][4])

        if len(p) == 6:

            if p[5][0] == 'Literal':
                p[0] = spsstructs.SPSLiteral(p[5][1], (p[1], p[3]),
                                             spsstructs.SPSCellContent(p[5][2], p[5][3]),
                                             p[4])
            if p[5][0] == 'Query':
                p[0] = spsstructs.SPSQuery(p[5][1], (p[1], p[3]),
                                           spsstructs.SPSCellContent(p[5][2], p[5][3]),
                                           p[5][4], p[4])

        if len(p) == 7:

            if p[6][0] == 'Literal':
                p[0] = spsstructs.SPSLiteral(p[6][1], (p[1], p[3]),
                                             spsstructs.SPSCellContent(p[6][2], p[6][3], p[4]),
                                             p[5])
            if p[6][0] == 'Query':
                p[0] = spsstructs.SPSQuery(p[6][1], (p[1], p[3]),
                                           spsstructs.SPSCellContent(p[6][2], p[6][3], p[4]),
                                           p[6][4], p[5])

    # cells can be given either explicitly, e.g., $H27 or with a variable such
    # as $query.personal_data.sw. Additionally, an offset might be applied if
    # desired in the form "+ (coloffset, rowoffset)"
    def p_celldec(self,p):
        '''celldec : CELL
                   | VARIABLE
                   | CELL PLUS LPARENTHESIS NUMBER COMMA NUMBER RPARENTHESIS
                   | VARIABLE PLUS LPARENTHESIS NUMBER COMMA NUMBER RPARENTHESIS'''

        # given either explicitly or with a variable and no offset
        if len(p) == 2:
            p[0] = spsstructs.SPSCellReference(p[1][1:])

        # given either explicitly or with a variable and an offset
        else:
            p[0] = spsstructs.SPSCellReference(p[1][1:], p[4], p[6])

    # attributes serve to set up the format of a cell or a range of cells
    def p_attributes(self, p):
        '''attributes : LSQUAREBRACKET attribute_list RSQUAREBRACKET'''

        # a list of attributes is stored as an instance of SPSCellAttribute
        # computed from a dictionary of pairs key/value
        p[0] = spsstructs.SPSCellAttribute(p[2])

    # attributes are given as a comma-separated list of attributes
    def p_attribute_list(self, p):
        '''attribute_list : attribute
                          | attribute COMMA attribute_list'''

        # the result is returned as a dictionary: If only one attribute is
        # given, it is immediately returned. Otherwise, the dictionary is
        # extended with the keys/values given in the list of attributes
        if len(p) == 4:
            p[1].update(p[3])

        p[0] = p[1]

    # a single attribute is given in the form <attribute> : <value>, where the
    # attribute is characterized as an id, but the value can contain different
    # characters
    def p_attribute(self, p):
        '''attribute : ID COLON NUMBER
                     | ID COLON STRING'''

        # in case it is a string, remove the quotes
        if isinstance(p[3], str):
            p[0] = {p[1] : p[3][1:-1]}
        else:
            p[0] = {p[1] : p[3]}

    # contents can be either instances of the basic types (integers, reals,
    # strings, datetimes or dates), literals or queries
    def p_content(self, p):
        '''content : DATETIMEEXP SEMICOLON
                   | DATEEXP SEMICOLON
                   | REAL SEMICOLON
                   | NUMBER SEMICOLON
                   | STRING SEMICOLON
                   | LITERAL DOT ID SEMICOLON
                   | QUERY DOT ID SEMICOLON'''

        # this grammar rule returns a tuple with the type of content (either a
        # literal or a query), and its value. If literal/query declarations were
        # used, they are substituted here. This rule returns a 4-tuple:
        #
        #         (Literal/Query, Name, Contents, Type)
        # where:
        #
        #    Name is given only with named literals, of course
        #
        #    Type is either 'datetime', 'date', 'real', 'integer', 'text' and
        #    'formula' i.e., those recognized by sqlite3 and, additionally,
        #    'formula's
        #
        # In case it refers to a query, it also adds a fifth value with the
        # database to use if any is provided
        if len(p) == 3:

            # now, distinguish among the different unnamed literals that can be
            # used
            if isinstance(p[1], datetime.datetime):
                p[0] = ('Literal', None, p[1], 'datetime')
            if isinstance(p[1], datetime.date):
                p[0] = ('Literal', None, p[1], 'date')
            if isinstance(p[1], float):
                p[0] = ('Literal', None, p[1], 'real')
            if isinstance(p[1], int):
                p[0] = ('Literal', None, p[1], 'integer')
            if isinstance(p[1], str):
                if p[1] == '=':
                    p[0] = ('Literal', None, p[1][1:-1], 'formula')
                else:
                    p[0] = ('Literal', None, p[1][1:-1], 'text')

        # in case either named literals or queries are been used ...
        if len(p) == 5:

            if p[1] == 'literal':

                if p[3] not in self._literal_table:
                    LOGGER.error(ERROR_UNKNOWN_LITERAL.format(p[3]))
                    sys.exit(0)

                p[0] = ('Literal', p[3], self._literal_table[p[3]],
                        spsstructs.get_type(self._literal_table[p[3]]))
            else:

                if p[3] not in self._query_table:
                    LOGGER.error(ERROR_UNKNOWN_QUERY.format(p[3]))
                    sys.exit(0)

                # note that queries are always of type 'text'. However, its type
                # is checked so that SPSQuery can check it if needed
                p[0] = ('Query', p[3], self._query_table[p[3]],
                        spsstructs.get_type(self._query_table[p[3]]),
                        self._query_db[p[3]])


    # in case a command is given wrt a region, its contents can be replicated
    # either to the right or downwards
    def p_direction(self, p):
        '''direction : RIGHT
                     | DOWN'''

        p[0] = p[1]


    # error handling
    # -----------------------------------------------------------------------------
    # Error rule for syntax errors
    def p_error(self, p):
        LOGGER.error(ERROR_SYNTAX_ERROR.format(p.lineno, p.value, p.type))
        sys.exit()


# -----------------------------------------------------------------------------
# VerbatimSPSParser
#
# Class used to process a verbatim string
# -----------------------------------------------------------------------------
class VerbatimSPSParser(SPSParser):
    """
    Class used to process a verbatim string
    """

    def run(self, data):
        """
        Just parse the given string
        """

        return self._parser.parse(data, lexer=self._lexer)


# -----------------------------------------------------------------------------
# InteractiveSPSParser
#
# Class used to run the parser in interactive mode
# -----------------------------------------------------------------------------
class InteractiveSPSParser(SPSParser):
    """
    Class used to run the parser in interactive mode
    """

    def run(self):
        """
        Enter a never-ending loop processing input as it comes
        """

        while True:
            try:
                spsinput = input('sps> ')
            except EOFError:
                break
            if not spsinput:
                continue
            return self._parser.parse(spsinput, lexer=self._lexer)


# -----------------------------------------------------------------------------
# FileSPSParser
#
# Class used to parse the contents of the given file
# -----------------------------------------------------------------------------
class FileSPSParser(SPSParser):
    """
    Class used to parse the contents of the given file
    """

    def run(self, filename):
        """
        Just read the contents of the given file and process them
        """

        with open(filename, encoding="utf-8") as stream:

            return self._parser.parse(stream.read(), lexer=self._lexer)





# Local Variables:
# mode:python
# fill-column:80
# End:
