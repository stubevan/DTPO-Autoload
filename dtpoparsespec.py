#!/usr/bin/python                                     #pylint: disable-msg=C0103
"""
Module which manages the details used to search for the details used to
create appropriate file name

This creates a list of FileDetails which are used to drive the search
"""

import re

from utilities import dtpo_log
from dtpoexceptions import DTPOFileError, ParseError

class SearchDetails(object) :                         #pylint: disable-msg=R0903
    """
    Holds the details of an object being searched for
    key_pattern   - the reg exp of the trigger pattern - e.g. "Statement Date"
    value_pattern - the reg exp we're looking for
    offset_line   - the offset (+ve or -ve) from the line of the key

    Created by Parsing the appropriate text
    """

    def __init__(self, value = None, key_pattern = None, value_pattern = None,
                 offset_line = None) :
        """
            Init class for the object.  Can create either with direct values
            (used by the test class) or from a string which is then parsed
        """

        if value is None :
            assert key_pattern is not None

            self.key_pattern = key_pattern
            self.value_pattern = value_pattern
            self.offset_line = offset_line
        else :
            assert (
                key_pattern is None and
                value_pattern is None and
                offset_line is None)

            self.key_pattern = None
            self.value_pattern = None
            self.offset_line = 0

            assert value

            #   Check if the offset is specified and then look for no offset
            #   search1 is looking for an offset specified in brackets after ->
            #   search2 is looking for "->"
            #   if neither are found then the value is the search string
            #   if search1 is set then we ignore search2
            search1 = re.search(
                '^([^#]*)->\(([\-+0-9]+)\)([^#]*)',    #pylint:disable-msg=W1401
                value.lstrip())
            search2 = re.search('^([^#]*)->([^#]*)', value.lstrip())

            if (not search1 and not search2) :
                #   No offset specified so just take whole pattern
                self.key_pattern = value
            elif (not search1 and search2) :
                self.key_pattern = search2.group(1)
                self.offset_line = 0
                self.value_pattern = search2.group(2)
                #   Just check for the edge case where a non numeric offset
                #   has been specced
                if (self.value_pattern[0] == '(') :
                    raise ParseError("Bad offset spec '{0}' - must be numeric"\
                                     .format(self.value_pattern))
            else :
                self.key_pattern = search1.group(1)
                try :
                    self.offset_line = int(search1.group(2))
                except ValueError as convert_error :
                    raise ParseError("Bad offset spec '{0}' caused error '{1}" \
                        .format(search1.group(2), str(convert_error)))
                self.value_pattern = search1.group(3)

            #   validate that the search patterns are valid
            if self.key_pattern is not None :
                try :
                    re.compile(self.key_pattern)
                except Exception as compile_exception :#pylint:disable-msg=W0703
                    raise ParseError("Bad Pattern in key -> '{0}' -> '{1}'" \
                        .format(self.key_pattern, compile_exception.message))

            if self.value_pattern is not None:
                try :
                    re.compile(self.value_pattern)
                except Exception as compile_exception :#pylint:disable-msg=W0703
                    raise ParseError("Bad Pattern in value -> '{0}' -> '{1}'" \
                        .format(self.value_pattern, compile_exception.message))

    def __ne__(self, other) :
        if not self.key_pattern == other.key_pattern :
            return "Expected '{0}' got '{1}".format(
                self.key_pattern, other.key_pattern)
        elif not self.value_pattern == other.value_pattern :
            return "Expected '{0}' got '{1}".format(
                self.value_pattern, other.value_pattern)
        elif not self.offset_line == other.offset_line :
            return "Expected '{0}' got '{1}".format(
                self.offset_line, other.offset_line)
        return False

    def __eq__(self, other) :
        if self != other :
            return False
        else :
            return True


class FilePattern (object) :                          #pylint: disable-msg=R0903
    """
    Holds the details of the of a particular kind of file
    e.g. Sole Bank Statement
    """

    def __init__(self) :
        self.database = None
        self.group = None
        self.tag = None
        self.description = None
        self.string1_pattern = None
        self.string2_pattern = None
        self.date_pattern = None

        # List for tracking what's been set
        self.var_list = []
        self.master = False

def parse_line(line, line_number) :
    """
    Parse a line to extract a key and value and return a key, value tuple
    """

    dtpo_log('debug', "%04d -> '%s'", line_number, line)

    #   Want lines that dont start with #
    search = re.match('(^[^#]*)::(.[^#]*)', line.lstrip())

    return_value = (False, "")

    # if we found something then
    if (search) :
        key = search.group(1).lstrip()
        value = search.group(2).rstrip()

        dtpo_log('debug', "key -> '%s', value -> '%s'", key, value)

        return_value = (key, value)

    return return_value

class DTPOParseSpec (object) :
    """
Parse the config file which  the patterms detailing how to search files
Goal is a filed document with the name YYYY-MM-DD {Pattern 1} {Pattern 2}.type
DefaultTag::Action Required	 -- Optional tag to add to each document
DefaultGroup::Inbox			 -- Mandatory
DefaultDatabase::Home Filing -- Mandatory

Database::Home Filing
Description::First Direct Sole Account	-- Comment [Optional]
Group::Finance/First Direct/Statements/Sole	-- Group Hierarchy
Pattern1::[match pattern]->(+/- offset)value pattern
    -- Regular express to look for followed by optional target which specifes
    -- end pattern.  If no target is specifed then the results of the first
    -- pattern become the target
Pattern2:: .... as Pattern 1
Date:: as Pattern 1
    """
    #   Define the grammar we want
    #                        type, default value, optional, variable
    pattern_keys = {
        'DefaultTag' : {'type' : 'default',
                        'default' : '',
                        'optional' : True,
                        'variable' : 'default_tag',
                        'precedence' : None},
        'DefaultGroup' : {'type' : 'default',
                            'default' : None,
                            'optional' : False,
                            'variable' : 'default_group',
                            'precedence' : None},
        'DefaultDatabase' : {'type' : 'default',
                            'default' : None,
                            'optional' : False,
                            'variable' : 'default_database',
                            'precedence' : None},
        'Database' : {'type' : 'value',
                        'default' : 'DefaultDatabase',
                        'optional' : True,
                        'variable' : 'database',
                        'precedence' : 'Slave'},
        'Tag' : {'type' : 'value',
                'default' : 'DefaultTag',
                'optional' : True,
                'variable' : 'tag',
                'precedence' : None},
        'Group' : {'type' : 'value',
                   'default' : 'DefaultGroup',
                   'optional' : True,
                   'variable' : 'group',
                    'precedence' : 'Slave'},
        'Description' : {'type' : 'value',
                        'default' : '',
                        'optional' : True,
                        'variable' : 'description',
                        'precedence' : None},
        'Pattern1' : {'type' : 'pattern',
                        'default' : None,
                        'optional' : False,
                        'variable' : 'string1_pattern',
                        'precedence' : 'Master'},
        'Pattern2' : {'type' : 'pattern',
                        'default' : None,
                        'optional' : True,
                        'variable' : 'string2_pattern',
                        'precedence' : None},
        'Date' : {'type' : 'pattern',
                    'default' : None,
                    'optional' : True,
                    'variable' : 'date_pattern',
                    'precedence' : None}
    }

    def __init__(self, config_file) :
        """
            read through the file and set the parameters
        """
        dtpo_log('debug', 'DTPOParseSpec. Source File -> %s', config_file)

        self.default_database = None
        self.default_group = None
        self.default_tag = None
        self.file_pattern_list = []
        self.string1_search_dict = {}
        self.string2_search_dict = {}
        self.date_search_dict = {}

        self.parse_pattern_file(config_file)

        self.create_reference_lists()

    def create_reference_lists(self) :
        """
            Called once everything is finished.  To make parsing easier we
            create sub lists which refer into the relevant SearchPatterns
        """

        counter = 0
        for file_pattern in self.file_pattern_list :
            search1 = file_pattern.string1_pattern
            search2 = file_pattern.string2_pattern
            date_search = file_pattern.date_pattern

            self.string1_search_dict[counter] = search1
            if search2 is not None :
                self.string2_search_dict[counter] = search2
            if date_search is not None :
                self.date_search_dict[counter] = date_search
            counter += 1

    def set_default(self, key, value) :
        """
        Set the appropriate default value
        """

        if key == 'DefaultDatabase' :
            self.default_database = value
        elif key == 'DefaultTag' :
            self.default_tag = value
        elif key == 'DefaultGroup' :
            self.default_group = value
        else :
            raise ValueError("DTPOParseSpec.set_default.  Bad key '{0}" \
                             .format(key))

    def check_file_pattern_complete(self,
        current_file_pattern) :
        """
            Called when a duplicate Trigger value is parsed
            Fill in the defaults and then check that we're valid

            Warning about current_file_pattern is disabled because we evaluate
            dynamically using eval
        """
        assert current_file_pattern is not None

        for key in self.pattern_keys :
            key_type = self.pattern_keys[key]['type']
            key_default = self.pattern_keys[key]['default']
            key_optional = self.pattern_keys[key]['optional']
            key_variable = self.pattern_keys[key]['variable']

            if key_type != 'default' :
                value = eval("current_file_pattern." + key_variable)

                if value is None :
                    if not key_optional :
                        raise ParseError("Missing mandatory {0} key '{1}'" \
                            .format(key_type, key))
                    else:
                        #   Set the default - if specified
                        if not key_default is None :
                            if key_default == '' :
                                exec(                 #pylint: disable-msg=W0122
                                    "current_file_pattern.{0} = ''".format(
                                    key_variable))
                            else :
                                assert key_default in self.pattern_keys
                                default_var = \
                                    self.pattern_keys[key_default]['variable']
                                exec(                 #pylint: disable-msg=W0122
                                    "current_file_pattern.{0} = self.{1}" \
                                     .format(key_variable, default_var))

    def process_pattern_value(self, current_file_pattern, key, value) :
        """
        We've got a line which contains a  pattern definition.
        current_file_pattern contains the entry beng worked on (could be empty)
        If necessary a new one is created and the previous one added to the
        pattern list
        """

        assert key is not None
        assert value is not None

        #   Check whether we've been given a valid key
        if not key in self.pattern_keys :
            raise ParseError("Unexpected key -> '" + key + "'")

        if not current_file_pattern :
            current_file_pattern = FilePattern()

        #   Get the key details
        key_type = self.pattern_keys[key]['type']
        key_variable = self.pattern_keys[key]['variable']
        key_precedence = self.pattern_keys[key]['precedence']

        if key_type == 'default' :
            # Global defaults - these can't be repeated
            current_value = eval("self." + key_variable)
            if current_value is not None :
                raise ParseError("Duplicate default {0}.  Now '{1}', " \
                    "new value '{2}'".format(key, current_value, value))
            # Now set the default
            exec("self.{0} = '{1}'".format(           #pylint: disable-msg=W0122
                key_variable, value))
        else :
            # Value or Pattern - if already set then triggers off a new entry
            # Our consistency checking will reject if it's been set
            # inappropriately

            #   Check if the master is set and this is a slave
            if current_file_pattern.master and key_precedence is not None :
                self.check_file_pattern_complete(current_file_pattern)
                self.file_pattern_list.append(current_file_pattern)
                current_file_pattern = FilePattern()
            else :
                if key in current_file_pattern.var_list :
                    current_value = eval("current_file_pattern." + key_variable)
                    raise ParseError("Duplicate key '{0}', current value '{1}" \
                        ", new value '{2}'".format(key, current_value, value))

            # set the variable - this also takes care of patterns
            self.set_file_pattern_variable(current_file_pattern, key, value)
        return current_file_pattern

    def set_file_pattern_variable(self, current_file_pattern, key, value) :
        """
        Set the appropriate file pattern variable.  This includes parsing the
        patterns
        """
        assert current_file_pattern
        assert value is not None

        key_variable = self.pattern_keys[key]['variable']
        key_type = self.pattern_keys[key]['type']
        key_precedence = self.pattern_keys[key]['precedence']

        current_file_pattern.var_list.append(key)

        if key_precedence == 'Master' :
            current_file_pattern.master = True

        if key_type == 'value' :
            exec(                                     #pylint: disable-msg=W0122
                "current_file_pattern.{0} = '{1}'".format(
                    key_variable, value))
        elif key_type == 'pattern' :
            exec(                                     #pylint: disable-msg=W0122
                "current_file_pattern.{0} = SearchDetails(value=value)".format(
                    key_variable))
        else :
            raise ValueError("Bad key ''{0}".format(key))

    def parse_pattern_file(self, config_file) :
        """
        Parse the file extracting the relevant details
        """
        #
        #	Now read through the file and set the parameters
        #
        current_file_pattern = None

        dtpo_log('debug', "Parsing pattern file -> '%s'", config_file)
        line_number = 0
        try :
            for line in open(config_file) :

                line_number = line_number + 1
                key, value = parse_line(line, line_number)

                # if we found something then process it
                if (key or value) :
                    current_file_pattern = self.process_pattern_value(
                            current_file_pattern,
                            key,
                            value)

            #   check that the defaults are there - do this first in case the
            #   file is corrupt - that way we fail gracefully
            for key in self.pattern_keys :
                if self.pattern_keys[key]['type'] == 'default' and \
                    not self.pattern_keys[key]['optional'] and \
                    eval("self.{0} is None".format(
                        self.pattern_keys[key]['variable'])) :
                    raise DTPOFileError(config_file, line_number,
                        "Missing default -> '{0}'".format(key))

            #   Validate that the last record is good & then add it to the list
            self.check_file_pattern_complete(current_file_pattern)
            self.file_pattern_list.append(current_file_pattern)


        except ParseError as parse_exception :
            raise DTPOFileError(
                config_file, line_number, parse_exception.message)

        except IOError as io_exception :
            #	Failed to access the config file
            raise DTPOFileError (config_file, 0,
                "Error accessing config file -> '{0}'" \
                .format(str(io_exception)))

    def get_file_pattern_list(self) :                 #pylint: disable-msg=C0111
        return self.file_pattern_list