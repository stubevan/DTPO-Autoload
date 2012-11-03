#!/usr/bin/python

""" Exceptions used by File Parser
"""

import sys


class ParseError(Exception) :
    """ Exception raised while parsing config files
    """

    def __init__(self, error_file, line_number, message) :
        self.args = (error_file, line_number, message)
        self.file = error_file
        self.line_number = line_number
        self.message = message

        Exception.__init__(self)


def main() :
    """ Test for ParseError
    """

    try :
        raise ParseError("/tmp/test", 1000, "Test Exception Message")

    except ParseError as parse_error :
        if type(parse_error) is ParseError:
            print "file -> '%s', line number -> %04d, message -> '%s'" % (
                parse_error.file, parse_error.line_number, parse_error.message)
if __name__ == '__main__':
    sys.exit(main())