#!/usr/bin/env python                                 #pylint: disable-msg=C0103
"""
    Test suite for TextExtractor
"""
import os

from dtpoexceptions import DTPOFileError
from text_extractor import TextExtractor

import unittest

class TextExtractorTest (unittest.TestCase) :         #pylint: disable-msg=R0904
    """
        Run a series of files through the converter to check the response
    """

    test_directory = None

    def setUp(self) :
        """
        Set up the config details
        """
        pass

    def test_bad_file(self) :
        """
            Self Explanatory!!!
        """
        self.assertRaises(DTPOFileError, TextExtractor, source_file = 'Wrong',
                          source_directory='/tmp',
                          working_directory = '/tmp',
                          testing = True)

    def test_inaccessible_file(self) :
        """
            Self Explanatory!!!
        """
        file_name = 'forbidden.pdf'
        self.assertRaises(DTPOFileError, TextExtractor, source_file = file_name,
                          source_directory= TextExtractorTest.test_directory,
                          working_directory = '/tmp',
                          testing = True)

    def test_empty_pdf(self) :
        """
            Access an empty file with .pdf suffix
            This could well break when we test the file type properly
        """
        file_name = 'empty_file.pdf'
        self.assertRaises(DTPOFileError, TextExtractor, source_file = file_name,
                          source_directory= TextExtractorTest.test_directory,
                          working_directory = '/tmp',
                          testing = True)

    def test_non_ocr_pdf(self) :
        """
            Access an valid pdf which hasn't been OCR'd
        """
        file_name = 'non_ocr_file.pdf'

        text_extractor = TextExtractor(
            source_file = file_name,
            source_directory= TextExtractorTest.test_directory,
            working_directory = '/tmp',
            testing = True)

        actual_results = text_extractor.get_file_contents_as_array()

        self.assertEquals(len(actual_results), 0)

    def test_valid_pdf(self) :
        """
            Access an empty file with .pdf suffix
            This could well break when we test the file type properly
        """

        expected_results = [
            'Test 1\n',
            'Test 2\n',
            '\n'
        ]
        file_name = 'test_file1.pdf'

        text_extractor = TextExtractor(
            source_file = file_name,
            source_directory= TextExtractorTest.test_directory,
            working_directory = '/tmp',
            testing = True)

        actual_results = text_extractor.get_file_contents_as_array()

        self.assertEquals(expected_results, actual_results)

if __name__ == '__main__':

    TextExtractorTest.test_directory = os.getenv('TEST_DIRECTORY')

    if TextExtractorTest.test_directory is None :
        raise ValueError ("FATAL - test_directory not specified")

    unittest.main()