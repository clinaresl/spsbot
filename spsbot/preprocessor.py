#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# preprocessor.py
# Description: Preprocessor of configuration files for parsing templates
# -----------------------------------------------------------------------------
#
# Started on  <Fri Apr 03 15:22:40 2020 >
# -----------------------------------------------------------------------------
#
# Carlos Linares Lopez
# Login   <carlos.linares@uc3m.es>
#

"""
Preprocessor of configuration files for parsing templates
"""

# imports
# -----------------------------------------------------------------------------
from string import Template

import re


# globals
# -----------------------------------------------------------------------------

# --regexp
REGEXP_TEMPLATE = r"template\s+[a-zA-Z0-9_]+\s*\(\s*\w*(,\s*\w+)*\s*\)\s*\{[^\}]+\}"
REGEXP_TEMPLATE_GROUPS = r"template\s+(?P<name>[a-zA-Z0-9_]+)\s*\(\s*(?P<args>\w*(,\s*\w+\s*)*)\s*\)\s*\{(?P<body>[^\}]+)\}"

# the following regexp is to be used with string.Template for substituting the
# name of each template
REGEXP_TEMPLATE_CALL = r"$name\s*\(\w*(,\s*\w+\s*)*\)"
REGEXP_ARGS = r"\(\s*(?P<args>\w*(,\s*\w+\s*)*)\s*\)"

# --errors
TEMPLATE_SYNTAX_ERROR = "Syntax error in template {0}"
ERROR_MISMATCHED_ARGS = "Mismatched number of arguments of template {0}: {1}"

# functions
# -----------------------------------------------------------------------------

def subst_template(text, itemplate):
    """returns the result of substituting all references to the given template in
       the specified text

    """

    # create a regular expression for matching invocations of this specific
    # template
    regexp = Template(REGEXP_TEMPLATE_CALL).substitute(name=itemplate.get_name())

    # look for calls to this template using the previous regular expression
    for imatch in re.finditer(regexp, text):

        # search for the values of all arguments
        jmatch = re.search(REGEXP_ARGS, imatch.group())
        if jmatch:

            # strip whitespaces before and after every argument and make sure to
            # remove empty arguments as well
            args = [iarg.strip(' \r\n\t\f\v') for iarg in jmatch.group('args').split(',')]
            args = [iarg for iarg in args if len(iarg) > 0]

            # and perform the substitution
            text = text.replace(imatch.group(),
                                itemplate.substitute(args))

    # and return the new text after performing all substitutions
    return text


# -----------------------------------------------------------------------------
# PRGTemplate
#
# Provides the definition of text templates and means for executing them
# -----------------------------------------------------------------------------
class PRGTemplate:
    """
    Provides the definition of text templates and means for executing them
    """

    def __init__(self, template):
        """a template is initialized with a textual description of it"""

        # copy the definition of the template
        self._template = template

        # initialize the different parts of every template
        self._name = ""
        self._args = []
        self._body = ""

        # and now process the contents of this template
        self._parse_template()


    def __str__(self):
        """provides a human readable version of the contents of this instance"""

        return """ template %s (%s): {%s}""" % (self._name,
                                                self._args,
                                                self._body)


    def _parse_template(self):
        """parses the different parts of the definition of this template to get its
           components: name, list of arguments and body

        """

        # at this point it is assumed that the template is correctly defined,
        # i.e., there are no syntax errors. If not, an exception is immediately raised
        regexp = re.compile(REGEXP_TEMPLATE_GROUPS, re.DOTALL)
        imatch = re.match(regexp, self._template)
        if imatch:

            # get right away the name and body
            self._name = imatch.group('name')
            self._body = imatch.group('body')

            # and process the arguments. For this, split them by the commas and
            # then remove all leading and trailing whitespaces (in any form)
            self._args = [iarg.strip(' \r\n\t\f\v') for iarg in imatch.group('args').split(',')]

            # make sure to remove all empty entries in the arguments
            self._args = [iarg for iarg in self._args if len(iarg) > 0]

            # surround the args with __ so that they can be used directly when
            # performing substitutions
            self._args = ["__" + iarg + "__" for iarg in self._args]

        else:
            raise ValueError(TEMPLATE_SYNTAX_ERROR.format(self._template))


    def get_name(self):
        """return the name of this template"""

        return self._name


    def get_args(self):
        """return the arguments of this template"""

        return self._args


    def get_body(self):
        """return the body of this template"""

        return self._body


    def substitute(self, args):
        """return the result of substituting all the given arguments in this template.
           Arguments to substitute within this template are identified between
           underscores

        """

        result = self._body

        # first things first, verify that the number of arguments given match
        # the number of arguments of this template
        if len(args) != len(self._args):
            raise ValueError(ERROR_MISMATCHED_ARGS.format(self._name, args))

        # create a dictionary to make the assignment of all arguments of this
        # template to the arguments given and perform every substitution as many
        # times as they appear in the text
        for key, value in dict(zip(self._args, args)).items():
            result = result.replace(key, value)

        # and return the result
        return result


# -----------------------------------------------------------------------------
# PRGProcessor
#
# Processes a configuration file to extract and substitute templates
# -----------------------------------------------------------------------------
class PRGProcessor:
    """Processes a configuration file to extract and substitute templates

    Templates are first processed and substitutions performed later. As a
    consquence, there is no need to declare the templates before they are used.

    """

    def __init__(self, configfile):
        """a preprocessor is initialized just with a configuration file whose contents
           are processed"""

        # copy the attributes
        self._configfile = configfile

        # open the file and retrieve all contents
        with open(self._configfile, encoding="utf-8") as fstream:
            self._contents = fstream.read()

        # initialize the list of templates found in this configuration file
        self._templates = []

        # initialize also the text of the config file stripped of the templates
        self._text = ""

        # and look for all its templates
        self._find_templates()


    def _find_templates(self):
        """search for the definition of templates in the configuration file and updates
           the list of templates found in this configuration file. It also
           updates the contents of the config file after removing all the
           templates definition

        """

        # -- initialization
        index = 0

        # find all templates in the cofiguration file of this instance
        regexp = re.compile(REGEXP_TEMPLATE, re.DOTALL)
        for imatch in re.finditer(regexp, self._contents):

            # as this template might contain references to other templates, make
            # sure that this template is entirely substituted with previous
            # references to other templates if any is used. For this invoke
            # templates defined in this configuration file in the same order
            # they have been defined
            body = imatch.group()
            for itemplate in self._templates:
                body = subst_template(body, itemplate)

            # create a template with this definition after correctly
            # substituting references to other templates, if any, and add it to
            # the list of templates found in the configuration file
            self._templates.append(PRGTemplate(body))

            # now, extract the slice of text in the configuration file until the
            # beginning of this template from the previous location of the
            # index, and update the location of the index
            self._text += self._contents[index:imatch.start()]
            index = imatch.end() + 1

        # finally, copy the text after the last template
        self._text += self._contents[index:]


    def _subst_templates(self):
        """"substitute all references to all templates in the text of the configuration
            file

        """

        # for all templates
        for itemplate in self._templates:

            # and substitute this template
            self._text = subst_template(self._text, itemplate)


    def get_templates(self):
        """return a list with all templates found in this configuration file"""

        return self._templates


    def get_text(self):
        """"return the text of the configuration file after removing all templates and
            substituting them"""

        return self._text
