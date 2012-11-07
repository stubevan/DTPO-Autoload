#!/usr/bin/python                                    #pylint: disable-msg=C0103

""" Exceptions used by File Parser
"""

import sys


class ParseError(Exception) :
    """ Exception raised while parsing lines in config files
    """
    def __init__(self, message) :
        self.message = message
        Exception.__init__(self)


class DTPOFileError(Exception) :
    """ Exception raised while processing files
    """
    def __init__(self, error_file, line_number, message) :
        self.args = (error_file, line_number, message)
        self.file = error_file
        self.line_number = line_number
        self.message = message

        Exception.__init__(self)
