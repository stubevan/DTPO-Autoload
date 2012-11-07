#!/usr/bin/python                                    #pylint: disable-msg=C0103
"""
    Unit Test Suite for importintodtpo
"""
import os

from appscript import k

from dtpoparsespec import SearchDetails
from importintodtpo import search_pattern, execute_import
from importintodtpo import DTPOImportParameters
from dtpoexceptions import ParseError

import unittest

class ImportPatternTest (unittest.TestCase) :        #pylint: disable-msg=R0904
    """
        Tests for the parser have been implemented as unittests - makes it
        easier to validate whats going on
    """

    def setUp(self) :
        """
            Create a test file to be parsed
        """

        self.file_array = (
            'line 1 - Test Search Pattern - Random Test',
            'line 2 - Date 24 Jan 2010',
            'line 3 - Another thing to look for',
            'line 4 - A number to search for 987654321',
            'line 5 - Date 23/10/2013 embedded in test',
            'line 6 - Company Name',
            'line 7 - email badger@set.co.uk'
        )

    def test_search_simple_search_not_found(self) :
        """
            Basic search with text that won't be found
        """
        search_details = SearchDetails(key_pattern = 'Wont Find This')
        self.assertEquals(search_pattern(search_details, self.file_array, 2),
                          None)

    def test_search_simple_valid(self) :
        """
            Basic search with text that will be found
        """
        search_details = SearchDetails(key_pattern = 'Random Test')
        self.assertEquals(search_pattern(search_details, self.file_array, 0),
                          'Random Test')

    def test_search_extract_from_pattern1(self) :
        """
            Basic search with text that will be found
        """
        search_details = SearchDetails(key_pattern = 'line 6 - (.*)$')
        self.assertEquals(search_pattern(search_details, self.file_array, 5),
                          'Company Name')

    def test_search_simple_transform_pattern1(self) :
        """
            Basic search with text that will be found
        """
        search_details = SearchDetails(key_pattern = 'Random Test',
                                       value_pattern = '!!Target Name')
        self.assertEquals(search_pattern(search_details, self.file_array, 0),
                          'Target Name')

    def test_search_simple_transform_pattern1_empty_target(self) :
        """
            Basic search with text that will be found
        """
        search_details = SearchDetails(key_pattern = 'Random Test',
                                       value_pattern = '!!')
        self.assertRaises(ParseError, search_pattern,
                          search_details, self.file_array, 0)

    def test_search_pattern1_offset(self) :
        """
            Extended search with text that will be found
        """
        search_details = SearchDetails(key_pattern = 'Random Test',
                                       value_pattern = 'Date (.*)$',
                                       offset_line = 1)
        self.assertEquals(search_pattern(search_details, self.file_array, 0),
                          '24 Jan 2010')

    def test_search_pattern1_offset_fail(self) :
        """
            Extended search with text that will be found
        """
        search_details = SearchDetails(key_pattern = 'Random Test',
                                       value_pattern = 'Date Wibble',
                                       offset_line = 1)
        self.assertEquals(search_pattern(search_details, self.file_array, 0),
                          None)

    def test_search_bad_offset_positive(self) :
        """
            Extended search with text that will be found
        """
        search_details = SearchDetails(key_pattern = 'Random Test',
                                       value_pattern = 'Date Wibble',
                                       offset_line = 100)
        self.assertEquals(search_pattern(search_details, self.file_array, 0),
                          None)

    def test_search_bad_offset_negative(self) :
        """
            Extended search with text that will be found
        """
        search_details = SearchDetails(key_pattern = 'Random Test',
                                       value_pattern = 'Date Wibble',
                                       offset_line = -100)
        self.assertEquals(search_pattern(search_details, self.file_array, 0),
                          None)


class ImportIntoDTPOTest(unittest.TestCase) :
    """
    Test the pseudo applesript which does the actual load into DTPO
    """

    test_directory = None

    def setUp(self) :
        """
        Not Used
        """
        pass

    def test_load_good_file_into_dtpo(self) :
        """
            Loads a good file into a known database
        """

        file_name = 'test_file1.pdf'
        import_parameters = DTPOImportParameters(testing = True)
        import_parameters.database = ImportIntoDTPOTest.test_directory + \
                                     '/' + 'Test Database.dtBase2'
        import_parameters.group = 'Test Group'
        import_parameters.tags = 'Action Required'
        import_parameters.string1 = 'Test String 1'
        import_parameters.string2 = 'Test String 2'
        import_parameters.date_string = '2012-11-10'

        import_parameters.file_type = k.PDF_Document
        import_parameters.mime_type = 'application/pdf'

        import_parameters.source_file = ImportIntoDTPOTest.test_directory + \
                                        "/" + file_name

        self.assertEquals(execute_import(import_parameters), True)

    def test_load_bad_directory(self) :
        """
            Attempt to open a bad database
        """

        file_name = 'test_file1.pdf'
        import_parameters = DTPOImportParameters(testing = True)
        import_parameters.database = ImportIntoDTPOTest.test_directory + \
                                     '/' + 'Bad Database.dtBase2'
        import_parameters.group = 'Test Group'
        import_parameters.tags = 'Action Required'
        import_parameters.string1 = 'Test String 1'
        import_parameters.string2 = 'Test String 2'
        import_parameters.date_string = '2012-11-10'

        import_parameters.file_type = k.PDF_Document
        import_parameters.mime_type = 'application/pdf'

        import_parameters.source_file = ImportIntoDTPOTest.test_directory + \
                                        "/" + file_name

        self.assertRaises(ParseError, execute_import, import_parameters)

    def test_load_bad_file(self) :
        """
            Attempt to load a bad file
        """

        file_name = 'bad_file1.pdf'
        import_parameters = DTPOImportParameters(testing = True)
        import_parameters.database = ImportIntoDTPOTest.test_directory + \
                                     '/' + 'Test Database.dtBase2'
        import_parameters.group = 'Test Group'
        import_parameters.tags = 'Action Required'
        import_parameters.string1 = 'Test String 1'
        import_parameters.string2 = 'Test String 2'
        import_parameters.date_string = '2012-11-10'

        import_parameters.file_type = k.PDF_Document
        import_parameters.mime_type = 'application/pdf'

        import_parameters.source_file = ImportIntoDTPOTest.test_directory + \
                                        "/" + file_name

        self.assertRaises(ParseError, execute_import, import_parameters)

class DocumentNameTest(unittest.TestCase) :
    """
        Ensure that dates get correctly converted to the proper format
    """

    def test_simple_document_name(self) :
        """
            Only string 1 defined
        """

        string1 = 'string1'
        string2 = None
        date_string = None
        import_params = DTPOImportParameters(
            string1 = string1,
            string2 = string2,
            date_string = date_string,
            testing = True
        )

        doc_name = import_params.get_document_name()
        self.assertEquals(doc_name, string1)

    def test_2_pattern_no_date(self) :
        """
            2 strings no date
        """

        string1 = 'string1'
        string2 = 'string2'
        date_string = None
        import_params = DTPOImportParameters(
            string1 = string1,
            string2 = string2,
            date_string = date_string,
            testing = True
        )

        doc_name = import_params.get_document_name()
        self.assertEquals(doc_name, string1+ '-' + string2)

    def test_1_pattern_good_date(self) :
        """
            1 string and a good date
        """

        string1 = 'string1'
        string2 = None
        date_string = '24 May 2012'
        import_params = DTPOImportParameters(
            string1 = string1,
            string2 = string2,
            date_string = date_string,
            testing = True
        )

        doc_name = import_params.get_document_name()
        self.assertEquals(doc_name, '2012-05-24 ' + string1)

    def test_2_pattern_good_date(self) :
        """
            2 strings and a good date
        """

        string1 = 'string1'
        string2 = 'string2'
        date_string = '24 May 2012'
        import_params = DTPOImportParameters(
            string1 = string1,
            string2 = string2,
            date_string = date_string,
            testing = True
        )

        doc_name = import_params.get_document_name()
        self.assertEquals(doc_name, '2012-05-24 ' + string1 + '-' + string2)

    def test_1_pattern_bad_date(self) :
        """
            1 string and a bad date
        """

        string1 = 'string1'
        string2 = None
        date_string = '24 M a y 2012'
        import_params = DTPOImportParameters(
            string1 = string1,
            string2 = string2,
            date_string = date_string,
            testing = True
        )

        self.assertRaises(ParseError, import_params.get_document_name)


if __name__ == '__main__':

    ImportIntoDTPOTest.test_directory = os.getenv('TEST_DIRECTORY')

    if ImportIntoDTPOTest.test_directory is None :
        raise ValueError ("FATAL - test_directory not specified")

    unittest.main()
