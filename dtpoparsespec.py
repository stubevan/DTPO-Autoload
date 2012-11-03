#!/usr/bin/python  #pylint: disable-msg=C0103
"""
Module which manages the details used to search for the details used to
create appropriate file name

This creates a list of FileDetails which are used to drive the search
"""

import re

from utilities import Config
from dtpoexceptions import ParseError
#from exceptions import *


#
#   Parse the pattern file

class SearchDetails(object) :   #pylint: disable-msg=R0903
    """
    Holds the details of an object being searched for
    key_pattern   - the reg exp of the trigger pattern - e.g. "Statement Date"
    value_pattern - the reg exp we're looking for
    offset_line   - the offset (+ve or -ve) from the line of the key
    """

    def __init__(self) :
        key_pattern = ""           #pylint: disable-msg=W0612
        value_pattern = ""         #pylint: disable-msg=W0612
        offset_line = 0            #pylint: disable-msg=W0612


class FilePattern (object) :        #pylint: disable-msg=R0903
    """
    Holds the details of the of a particular kind of file
    e.g. Sole Bank Statement
    """

    def __init__(self) :
        self.database = ""
        self.group = ""
        self.tags = ""
        self.description = ""
        self.string1_details = False
        self.string2_details = False
        self.date_details = False

#
#   Check whether a pattern is valid - if not raise an exception
#
def check_pattern_record(file_pattern) :

    assert file_pattern
    error = False
    if not file_pattern.database :
        error = "check_pattern_record:  missing Database"
    elif not file_pattern.group :
        error = "check_pattern_record:  missing Group.  Database -> '" + \
                file_pattern.database + "'"
    elif not file_pattern.string1_details :
        error = "check_pattern_record:  primary search details missing, " \
                "Database -> '" + file_pattern.database + "', Group -> '" + \
                file_pattern.group + "'"
    elif not file_pattern.string1_details.key_pattern :
        error = "check_pattern_record:  internal inconsistency.  Search " \
                "details present but missing search pattern, Database -> '" \
                + file_pattern.database + "', Group -> '" + \
                file_pattern.group + "'"

    return error

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

    def check_if_new_pattern_record(self, key, value, file_pattern) :
        """
        See if this is a new record
        """

        assert file_pattern

        error_message = False
        #   Is this a new one
        if file_pattern.database == "" :
            if not key == 'Database' :
                error_message = "key -> '" + key + "' set before database"
                return error_message
            file_pattern.database = value

        # Triggers for a new entry are a new Database or Group
        elif key == 'Database' or (key == 'Group' and
                                   not file_pattern.group == "") :
            #   Already have a record in flight
            #   Check that the one being closed is complete
            error_message = check_pattern_record(file_pattern)
            if not error_message :
                self.file_pattern_list.append(file_pattern)
                file_pattern = FilePattern()
        elif key == 'Database' :
            file_pattern.database = value
        elif key == 'Group' :
            file_pattern.group = value
        elif key == 'Tag' :
            file_pattern.tag = value
        elif key == 'Description' :
            file_pattern.description = value
        return error_message

    def update_pattern_record(self, key, value,  #pylint: disable-msg=R0201
                              file_pattern,
                              search_details) :
        """
        Add a part of the record which has a pattern in it
        This will need further splitting as, it may have an offset specied in
        brackets
        """

        assert file_pattern
        assert search_details
        error_message = ""

        #	Pattern1::search pattern->(+/- lines)Pattern to extract target

        if (key == 'Pattern1') :
            file_pattern.string1_details = search_details
        elif (key == 'Pattern2') :
            file_pattern.string2_details = search_details
        elif (key == 'Date' ) :
            file_pattern.date_details = search_details
        else :
            Config.logger.fatal("Unexpected key in search_details -> '%s'", key)
            raise AssertionError()

        #   Check if the offset is specified and then look for no offset
        #   search1 is looking for an offset specified in brackets after ->
        #   search2 is looking for "->"
        #   if neither are found then the value is the search string
        #   if search1 is set then we ignore search2
        search1 = re.match('^([^#]*)->\((.*)\)([^#]*)', value.lstrip())
        search2 = re.match('^([^#]*)->([^#]*)', value.lstrip())

        if (not search1 and not search2) :
            #   No offset specified so just take whole pattern
            search_details.key_pattern = value
        elif (not search1 and search2) :
            search_details.key_pattern = search2.group(1)
            search_details.offset_line = 0
            search_details.value_pattern = search2.group(2)
        else :
            search_details.key_pattern = search1.group(1)
            search_details.offset_line = int(search1.group(2))
            search_details.value_pattern = search1.group(3)

        #   validate that the search patterns are valid
        if search_details.key_pattern :
            try :
                re.compile(search_details.key_pattern)
            except Exception as compile_exception :   #pylint: disable-msg=W0703
                error_message = "Bad Pattern in -> '" + key + "' -> '" \
                               + compile_exception.message + "'"

        if search_details.value_pattern :
            try :
                re.compile(search_details.value_pattern)
            except Exception as compile_exception :   #pylint: disable-msg=W0703
                error_message = "Bad Pattern in -> '" + key + "' -> '" \
                                + compile_exception.message + "'"

        return error_message

    def parse_pattern_file(self, config_file) :
        """
        Parse the file extracting the relevant details
        """
        #	Set up an array to make it easy to parse
        default_database = { 'value' : '', 'set' : False, 'repeated' : False }
        default_tag      = { 'value' : '', 'set' : False, 'repeated' : False }
        default_group    = { 'value' : '', 'set' : False, 'repeated' : False }

        database    = { 'value' : '', 'set' : False, 'repeated' : True,
                       'pattern' : False }
        group       = { 'value' : '', 'set' : False, 'repeated' : True,
                       'pattern' : False }
        tag         = { 'value' : '', 'set' : False, 'repeated' : True,
                       'pattern' : False }
        description = { 'value' : '', 'set' : False, 'repeated' : True,
                       'pattern' : False }

        pattern1 = { 'value' : '', 'set' : False, 'repeated' : True,
                    'pattern' : True }
        pattern2 = { 'value' : '', 'set' : False, 'repeated' : True,
                    'pattern' : True  }
        file_date = { 'value' : '', 'set' : False, 'repeated' : True,
                    'pattern' : True  }

        #   These are details set once
        global_parameters = {
            'DefaultTag' : default_tag,
            'DefaultGroup' : default_group,
            'DefaultDatabase' : default_database
        }

        #   These will be repeated and used to build up the spec
        pattern_parameters = {
            'Database' : database,
            'Tag' : tag,
            'Group' : group,
            'Description' : description,
            'Pattern1' : pattern1,
            'Pattern2' : pattern2,
            'Date' : file_date
        }

        #
        #	Now read through the file and set the parameters
        #
        current_file_pattern = FilePattern()

        Config.logger.info("Parsing pattern file -> '%s'", config_file)
        line_number = 0
        try :
            for line in open(config_file) :

                line_number = line_number + 1
                Config.logger.debug("%04d -> '%s'", line)

                #   Want lines that dont start with #
                search = re.match('(^[^#].*)::(.[^#]*)', line.lstrip())

                # if we found something then
                if (search) :
                    key = search.group(1).lstrip()
                    value = search.group(2).rstrip()

                    if (Config.logger) :
                        Config.logger.info("key -> '%s', value -> '%s'",
                                           key, value)

                    if (key in global_parameters) :
                        # Make sure it's not already set
                        if (global_parameters[key]['set']) :
                            error_message = "Duplicate key -> '" + key \
                            + "', now -> '" + str(value) + "', was '" + \
                            str(global_parameters[key]['value']) + "'"
                            raise ParseError(
                                config_file, line_number, error_message)

                        #   Set it
                        global_parameters[key]['value'] = value
                        global_parameters[key]['set'] = True

                    elif (key in pattern_parameters) :
                        #   File Spec
                        if (not pattern_parameters[key]['pattern']) :
                            error_message = self.check_if_new_pattern_record(
                                key, value, current_file_pattern)
                            if error_message :
                                raise ParseError(
                                    config_file, line_number, error_message)
                        else :
                            searchPattern = SearchDetails()
                            error_message = self.update_pattern_record(
                                key, value, current_file_pattern, searchPattern)
                            if error_message :
                                raise ParseError(
                                    config_file, line_number, error_message)
                    else :
                        error_message = "Unexpected key -> '" + key + "'"
                        raise ParseError(config_file, line_number,
                                         error_message)

        except IOError as io_exception :
            #	Failed to access the config file
            error_message = "Error accessing config file -> '" + \
                            str(io_exception) + "'"
            raise ParseError (config_file, 0, error_message)

        #
        #   Come out of the loop - before checking last record
        #   check that the defaults are there
        for key in global_parameters :
            if not global_parameters[key]['set'] :
                error_message = "Missing global default -> '" + key + "'"
                raise ParseError(config_file, line_number, error_message)

        #   Validate that the last record is good & then add it to the list
        error = check_pattern_record(current_file_pattern)
        if error :
            raise ParseError(config_file, line_number, error)

        self.file_pattern_list.append(current_file_pattern)

    def __init__(self, config_file) :

        self.success = False
        self.default_database = ""
        self.default_group = ""
        self.default_tags = ""
        self.file_pattern_list = []

        #
        #	Now read through the file and set the parameters
        #
        Config.logger.info("DTPOParseSpec. Source File -> %s", config_file)

        self.parse_pattern_file(config_file)


    def get_success(self) :
        return self.success

    def get_default_database(self) :
        return self.default_database

    def get_default_group(self) :
        return self.default_group

    def get_default_tags(self) :
        return self.default_tags

    def get_file_pattern_list(self) :
        return self.file_pattern_list
