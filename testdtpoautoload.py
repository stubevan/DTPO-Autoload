#!/usr/bin/python    #pylint: disable-msg=C0103
"""
    Script to test underlying modeules of dtpo auto load
"""

import imp
import sys
import re
import optparse

from utilities import Config
from  dtpoparsespec import DTPOParseSpec
from dtpoexceptions import ParseError

TEST_DEBUG = False

class ParseTest (object) :    #pylint: disable-msg=R0903
    """ Holds Test Details
    """

    def __init__ (self, test_goal, config_file,    #pylint: disable-msg=R0913
				  line_number, message, check_function) :
        self.test_goal = test_goal
        self.config_file = config_file
        self.line_number = int(line_number)
        self.message = message
        self.check_function = check_function

def build_test_list(config_test_directory,         #pylint: disable-msg=R0914
					config_test_file) :
    """
        Parse the config file to get the tests.  Format is seperated with "::"
        test_goal::config file::python file::expected line Number of error \
            (0) is success::expected error message

        the loader expects a file with the same name as the config file ".py"
        to contain a method called checkMethod
        this takes no parameters as config is global
    """

    if TEST_DEBUG :
        print "build_test_list config_test_directory -> {0}" \
            ", config_file -> {1}".format(
                config_test_directory, config_test_file)
    test_list = []
    test_number = 0
    line_number = 0
    config_file = config_test_directory + "/" + config_test_file

    try :
        for line in open(config_file) :
            line_number = line_number +1
            search = re.match('^([^#]*)', line.lstrip())
            config_line = search.group(1)

            if not config_line == "" :
                test_number = test_number + 1
                arg_list = config_line.split('::')

                if not len(arg_list) == 5 :
                    print "Invalid line in config file - # attributes != 5\n  "\
                        "line -> {0}:{1}".format(str(line_number), line)
                    raise SystemExit("FATAL ERROR Invalid config file")
                    #NOTREACHED

                test_goal = arg_list[0]
                test_config_file = config_test_directory + "/" + arg_list[1]
                test_python_file = config_test_directory + "/" + arg_list[2]
                errorline_number = int(arg_list[3])
                message = arg_list[4].rstrip()

                test_name = "check_function" + str(test_number)
                try :
                    check_function = imp.load_source(
                        test_name,
                        test_python_file)
                except Exception as exception:
                    print "Failed to load python file -> '{0}'" \
                        .format(test_python_file)
                    raise exception

                the_test_to_run = ParseTest(test_goal, test_config_file,
                                            errorline_number, message,
                                            check_function)
                test_list.append(the_test_to_run)
    except Exception as exception :
        print "Failed to process config file -> '" + config_file + "'"
        print "Error message -> '" + str(exception) + "'"
        raise exception

    return test_list

def run_the_test(class_to_test, test_number, the_test) :
    """
        Run a test - involves creating a config and then checking that if an
        error the exception is correct
        If the build is successful then need to check that values are correct
        involves running dynamic code!!
    """""

    print "Running test # {0}, Goal -> {1}".format(test_number,
                                                   the_test.test_goal)
    if TEST_DEBUG :
        print "Config File -> " + the_test.config_file

    success = True
    try :
        if class_to_test == "Config" :
            Config(the_test.config_file)
            success = the_test.check_function.checkMethod()
        elif class_to_test == "DTPOParseSpec" :
            pattern_spec = DTPOParseSpec(the_test.config_file)
            success = the_test.check_function.checkMethod(pattern_spec)
        else :
            #    Shouldn't be here
            print "TEST ERROR - Invalid class specified -> '{0}'" \
                .format(class_to_test)
            success = False
        #
        #    If we were successful then check that the values are correct
        #

        if not success :
            print "TEST FAILED object Failed Check Method"
        if success and TEST_DEBUG :
            print "Test Passed"

    except ParseError as parse_error :
        if not (type(parse_error) is ParseError):
            print "Unexpected exception -> " + str(parse_error)
            success = False
        else :
            if TEST_DEBUG :
                print "Caught Exception -> '{0}, line number -> {1}, message " \
                    "-> '{2}'".format(
                        parse_error.file,
                        parse_error.line_number,
                        parse_error.message)
            #
            #    Check whether its correct
            #
            if parse_error.message != the_test.message :
                print "TEST FAILED Bad Exception - Error messages don't match"
                print "Expected message ->" + the_test.message + "<-"
                print "got              ->" + str(parse_error.message) + "<-"
                success = False
            elif parse_error.line_number != the_test.line_number  :
                print "TEST FAILED Bad Exception.  Expected line Number " \
                    + str(the_test.line_number) + ", got -> " \
                    + str(parse_error.line_number)
                success = False

    return success


def test_class(class_to_test, config_test_directory, config_test_file,
               config_file="") :
    """
        Test function for config class
    """
    if TEST_DEBUG :
        print "Testing class    -> '" + class_to_test + "'"
        print "directory        -> '" + config_test_directory + "'"
        print "config_test_file -> '" + config_test_file + "'"
        print "config_file      -> '" + config_file +"'"

    try :
        test_list = build_test_list(config_test_directory, config_test_file)
        if config_file and config_file != "" :
            Config.config = Config(config_file)

    except Exception as exception:
        print "build_test_list Failed -> Tests Abandoned -> " + str(exception)
        raise exception


    test_number = 1
    failures = 0

    for test in test_list :
        if TEST_DEBUG :
            print "Running test -> " + str(test_number)

        if not run_the_test(class_to_test, test_number, test) :
            failures = failures + 1

        test_number = test_number + 1

    print "Completed test of -> {0}. {1} tests run. {2} failed".format(
        class_to_test,
        test_number - 1,
        failures)

def main() :
    """
        Run the testing
    """
    command_line_parser = optparse.OptionParser()
    command_line_parser.add_option(
        "--TEST_DEBUG", action="store_true", dest="TEST_DEBUG")
    command_line_parser.add_option(
        "--test_directory", action="store", dest="test_directory")
    command_line_parser.add_option(
        "--test_config", action="store_true", dest="test_config")
    command_line_parser.add_option(
        "--config_test_file", action="store", dest="config_test_file")
    command_line_parser.add_option(
        "--test_patterns", action="store_true", dest="test_patterns")
    command_line_parser.add_option(
        "--pattern_test_file", action="store", dest="pattern_test_file")
    command_line_parser.add_option(
        "--test_loader", action="store_true", dest="test_loader")
    command_line_parser.add_option(
        "--loader_test_file", action="store", dest="loader_test_file")
    command_line_parser.add_option(
        "--config_file", action="store", dest="config_file")

    command_line_parser.set_defaults(TEST_DEBUG=False)
    command_line_parser.set_defaults(test_config=False)
    command_line_parser.set_defaults(test_parser=False)
    command_line_parser.set_defaults(test_loader=False)
    command_line_parser.set_defaults(test_file_parse=False)

    opts, source_file_args = command_line_parser.parse_args()

    if (opts.TEST_DEBUG) :
        TEST_DEBUG = True
    #
    #    Config Directory is mandatory
    #
    if not opts.test_directory :
        raise SystemExit("FATAL ERROR config_test_directory not specified")

    #    Tests for the Config File
    #
    if (opts.test_config) :
        test_class("Config", opts.test_directory, opts.config_test_file)
    if (opts.test_patterns) :
        test_class("DTPOParseSpec", opts.test_directory, opts.pattern_test_file,
                   opts.config_file)

if __name__ == '__main__':
    sys.exit(main())
