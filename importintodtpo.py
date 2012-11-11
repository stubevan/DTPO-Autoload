#!/usr/bin/python                                     #pylint: disable-msg=C0103
"""
    Will probably split this in 2 - has methods to produce file name,
    parse PFD and then load in DTPO
"""

import re
from dateutil import parser
from time import sleep

from appscript import app

from dtpoexceptions import ParseError
#from dtpoparsespec import DTPOParseSpec
from utilities import dtpo_log, Config, dtpo_alert, basename
from text_extractor import TextExtractor

class DTPOImportParameters (object) :
    """
         Parameters required for an import
    """

    def __init__(self, pattern_spec = None, pattern_number = None,
                string1 = None, string2 = None, date_string = None,
                testing = False, source_file = None) :

        if not testing :
            assert pattern_spec
            self.pattern_spec = pattern_spec

            if string1 is not None :
                assert pattern_number is not None
                self.database = \
                    pattern_spec.file_pattern_list[pattern_number].database
                self.group = \
                    pattern_spec.file_pattern_list[pattern_number].group
                self.tags = \
                    pattern_spec.file_pattern_list[pattern_number].tag
            else:
                self.database = pattern_spec.default_database
                self.group = pattern_spec.default_group
                self.tags = pattern_spec.default_tag
        else :
            self.pattern_spec = None

            self.database = None
            self.group = None
            self.tags = None

        # Initialise variables that will get defined as the parse progresses
        self.string1 = string1
        self.string2 = string2
        self.date_string = date_string
        self.source_file = source_file

        self.file_type = None
        self.mime_type = None

    def get_document_name(self) :
        """
            creates the final name of the file by constructing from
            the component parts.
        """
        if self.string1 is None :
            self.string1 = 'No Match Found'

        document_name = ''

        if self.date_string is not None :
            #   We have a date - try and convert it into something meaningful
            try :
                dt = parser.parse(self.date_string)
                date_string = dt.strftime('%Y-%m-%d')
            except ValueError as date_error :
                message = "Failed to convert '{0}' to date -> {1}".format(
                    self.date_string, str(date_error))
                raise ParseError(message)
            except Exception as unknown_exception :
                message = "unknown exception while parsing date {0} -> {1}" \
                        .format(self.date_string, str(unknown_exception))

            document_name = date_string + " " + self.string1
        else :
            document_name = self.string1

        if self.string2 is not None :
            document_name = document_name + "-" + self.string2

        return document_name

    def print_import_details(self, source_file) :
        """
            Display the details of the file to be imported.
        """

        print "\nSource file -> {0}\n".format(source_file)
        print "Target details:"
        print "Database    -> {0}".format(self.database)
        print "Group       -> {0}".format(self.group)
        print "Tags        -> {0}".format(self.tags)
        print "Document    -> {0}\n".format(self.get_document_name())

def parse_source_file(text_extractor, pattern_spec) :
    """
        Now iterate through the file and see if we can find anything

        We're trying to avoide multiple parses of the file (we're looking for
        up to 3 patterns:  pattern 1, pattern 2 & date).  The algorithm is
        currently not efficient as we have to parse the file twice but
        given that most patterns will be found in the first few lines it's not
        that bad.  In addition it makes things considerably less complicated.
        Pattern 2 and date can "look back" and occur before pattern 1 so
        tracking that would make things harder to understand!!
    """
    assert pattern_spec

    found_string1 = None
    found_string2 = None
    found_date = None
    line_number = 0
    pattern_number = None

    #
    #   Iterate through the file for the first time looking for the primary
    #   pattern
    file_array = text_extractor.get_file_contents_as_array()
    for line_number in range(0, len(file_array)-1) :
        found_string1, pattern_number = search_pattern_list(
            pattern_spec.string1_search_dict,
            file_array,
            line_number)
        if found_string1 :
            # See if it's a special
            if found_string1 == 'SOURCE_FILE' :
                found_string1 = basename(text_extractor.source_file)
            break

    if found_string1 :
        #   We got something - see if there is a pattern2 and date to look for
        string2_search_details = None
        date_search_details = None

        if pattern_number in pattern_spec.string2_search_dict :
            string2_search_details = \
                pattern_spec.string2_search_dict[pattern_number]
        if pattern_number in pattern_spec.date_search_dict :
            date_search_details = \
                pattern_spec.date_search_dict[pattern_number]

        line_number = 0
        found_string2 = None
        found_date = None

        #   Assuming there is something to look for do the search
        while line_number < len(file_array)-1 and (
            (string2_search_details is not None and found_string2 is None ) or
            (date_search_details is not None and found_date is None)) :

            if string2_search_details is not None :
                found_string2 = search_pattern(
                    string2_search_details, file_array, line_number)
            if date_search_details is not None :
                found_date = search_pattern(
                    date_search_details, file_array, line_number)
            line_number += 1

    return DTPOImportParameters(pattern_spec = pattern_spec,
                                pattern_number = pattern_number,
                                source_file = text_extractor.source_file,
                                string1 = found_string1,
                                string2 = found_string2,
                                date_string = found_date)

def search_pattern_list(search_list, file_array, line_number) :
    """
        Iterate through search list and see if we can find a string
        This method is only used to search for the primary pattern
    """
    pattern_number = 0
    found_string = None

    while found_string is None and pattern_number < len(search_list) :
        found_string = search_pattern(
            search_list[pattern_number], file_array, line_number)
        pattern_number += 1

    return (found_string, pattern_number-1)

def search_pattern(search_details, file_array, line_number) :
    """
        Check whether a pattern can be extracted based on the passed list
        of SearchDetails.  We stop at the first one.  A reminder of the
        methodology.  This holds the details of an object being searched for
        key_pattern - the reg exp of the trigger pattern - e.g. "Statement Date"
            Note that if the reg exp returns a group then this will be used
        value_pattern - the reg exp we're looking for
        offset_line   - the offset (+ve or -ve) from the line of the key
    """
    assert search_details
    assert file_array

    found_string = None

    search_results = re.search(
        search_details.key_pattern, file_array[line_number])
    if search_results :
        #
        #   Got something - First Check if a hard target has been specified
        if (search_details.value_pattern is not None and
            search_details.value_pattern.find('!!') == 0) :
            found_string = search_details.value_pattern[2:]
            if found_string == '' :
                error_message = "Line {0}.  Empty hard target specified for " \
                    "pattern '{1}'".format(line_number,
                                           search_details.key_pattern)
                raise ParseError(error_message)

        #   is there a another value to look for
        elif search_details.value_pattern is not None :

            if search_details.offset_line is None:
                offset = 0
            else :
                offset = search_details.offset_line

            search_results = None

            if line_number + offset in range(0, len(file_array)-1) :
                if search_details.value_pattern is not None :
                    search_results = re.search(search_details.value_pattern,
                        file_array[line_number + offset])

    if found_string is None and search_results:
        #   Get the last group if its there
        group_id = 0
        if search_results.lastindex is not None :
            group_id = search_results.lastindex
        found_string = search_results.group(group_id)

    return found_string


def execute_import(import_parameters) :
    """
        Now run the actual import into DTPO
    """

    assert import_parameters.source_file
    assert import_parameters.file_type
    assert import_parameters.mime_type
    assert import_parameters.group
    assert import_parameters.tags

    source_file = import_parameters.source_file
    database = Config.config.get_database_directory() + '/' + \
        import_parameters.database
    document_name = import_parameters.get_document_name()

    dtpo_log('info', "execute_import source file -> %s", source_file)
    dtpo_log('info', "execute_import database -> %s", database)
    dtpo_log('info', "execute_import group -> %s", import_parameters.group)
    dtpo_log('info', "execute_import tags -> %s", import_parameters.tags)
    dtpo_log('info', "execute_import document name -> %s", document_name)

    try :
        try :
            dtpo_db = app(u'DEVONthink Pro').open_database(database)
            sleep(2)
            dtpo_db_id = dtpo_db.id()
        except AttributeError as attribute_error :
            message = "Failed to open database {0} -> {1}".format(
                import_parameters.database, str(attribute_error))
            raise ParseError(message)

        try :
            dtpo_group = app(u'DEVONthink Pro').create_location(
                import_parameters.group,
                in_=app.databases.ID(dtpo_db_id))
            # get the group to check that it's there
            dtpo_group_id = dtpo_group.id()           #pylint: disable-msg=W0612
        except AttributeError as attribute_error :
            message = "Failed access group {0} -> {1}".format(
                import_parameters.group, str(attribute_error))
            raise ParseError(message)

        try :
            doc = app(u'DEVONthink Pro').import_(
                import_parameters.source_file,
                name = document_name,
                to = dtpo_group)

            docid = doc.id()
        except AttributeError as attribute_error :
            message = "Failed import document {0} -> {1}".format(
                document_name, str(attribute_error))
            raise ParseError(message)

        try :
            app(u'DEVONthink Pro').databases.ID(
                dtpo_db_id).contents.ID(docid).unread.set(True)
            app(u'DEVONthink Pro').databases.ID(
                dtpo_db_id).contents.ID(docid).tags.set(import_parameters.tags)
            app(u'DEVONthink Pro').databases.ID(
                dtpo_db_id).contents.ID(docid).URL.set('')
            duplicate = app(u'DEVONthink Pro').databases.ID(
                dtpo_db_id).contents.ID(docid).number_of_duplicates.get()
            if int(duplicate) > 0 :
                dtpo_alert('warn', reason = '{0} duplicates of '\
                    .format(duplicate), file_name = document_name)
        except AttributeError as attribute_error :
            message = "Failed set attributes {0} -> {1}".format(
                import_parameters.get_document_name(), str(attribute_error))
            raise ParseError(message)

    except ParseError as parse_error:
        raise parse_error
    except Exception as exception :
        ex_type = type(exception)
        message = "Unexpected exception {0} -> {1}".format(
            ex_type, str(exception))
        raise Exception(message)

    return True

def get_import_parameters(source_file, pattern_spec, test_parse) :
    """
        Imports the specified file into DTPO using the spec given
    """

    dtpo_log('debug', "get_import_parameters source_file -> %s", source_file)

    #
    #   parse the file and turn it into a list
    #
    file_parser = TextExtractor(source_file, test_parse = test_parse)

    #   Parse the file and then do the import
    dtpo_import_parameters = parse_source_file(file_parser, pattern_spec)
    dtpo_import_parameters.file_type = file_parser.file_type
    dtpo_import_parameters.mime_type = file_parser.mime_type

    return dtpo_import_parameters
