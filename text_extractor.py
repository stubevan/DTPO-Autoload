#!/usr/bin/env python                                 #pylint: disable-msg=C0103
"""
    Text Extraction class
"""

import os

from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdftypes import PDFException

from appscript import k

from utilities import Config, dtpo_log
from dtpoexceptions import DTPOFileError

VALID_FILE_TYPES = (
    k.PDF_Document,
    k.html,
    k.rtf,
    k.txt,

)

class TextExtractor(object) :
    """
    Attempts to extract text from the passed file
    """

    def __init__(self,
                 source_file,
                 source_directory = None,
                 working_directory = None,
                 testing = False) :
        """
            source directory and working directory are generally for test
            purposes
        """

        if not testing :
            #   If this isn't specified we're testing so don't need them
            assert Config.logger
            assert Config.config

        dtpo_log('info', 'TextExtractor -> %s', source_file)

        if source_directory is None :
            source_directory = Config.config.get_source_directory()
        if working_directory is None :
            working_directory = Config.config.get_working_directory()

        self.source_file =  source_directory + "/" + source_file
        self.text_file = working_directory + "/" + source_file + ".txt"
        self.file_array = []
        self.status = False

        self.file_type, self.mime_type = get_file_type(self.source_file)
        if str(self.file_type) == 'k.PDF_Document' :
            self.parse_pdf()
        else :
            error_message = 'TextExtractor - Invalid File Type for {0}' \
                .format(self.source_file)
            dtpo_log('error', error_message)
            raise ValueError(error_message)

    def parse_pdf(self) :
        """
            Parse a PDF and return text contents as an array
        """

        dtpo_log('info', "parsePDF sourceFile -> '%s'", self.source_file)

        # input options
        pagenos = set()
        maxpages = 0
        # output option
        codec = 'utf-8'
        caching = True
        laparams = LAParams()

        rsrcmgr = PDFResourceManager(caching=caching)

        try :
            outfp = file(self.text_file, 'w')
        except IOError as io_error:
            raise DTPOFileError(self.text_file, 0, str(io_error))

        try :
            fp = file(self.source_file, 'rb')
        except IOError as io_error:
            raise DTPOFileError(self.source_file, 0, str(io_error))

        try :
            device = TextConverter(
                rsrcmgr, outfp, codec=codec, laparams=laparams)
            process_pdf(rsrcmgr, device, fp, pagenos, maxpages=maxpages,
                caching=caching, check_extractable=True)

        except PDFException as pdf_error :
            message = "Failed to parse PDF -> {0}".\
                      format(str(pdf_error))
            raise DTPOFileError(self.source_file, 0, message)
        except Exception as exception :
            message = "Failed to parse PDF file Unknown exception {0} - > {1}" \
                      .format(type(exception), str(exception))
            raise DTPOFileError(self.source_file, 0, message)

        fp.close()
        device.close()
        outfp.close()

        #   Got the PDF converted = now get it into an array
        self.file_array = []
        for line in open(self.text_file) :
            self.file_array.append(line)

        #   Remove the last entry - it's always '\x0c'
        if len(self.file_array) > 0:
            del self.file_array[-1]

        #   Remove the outfile
        os.remove(self.text_file)

    def get_file_contents_as_array(self) :
        """
        Even if there was nothing to convert there the array will be empty
        """
        return self.file_array

def get_file_type(source_file) :
    """
        Check the source file and determine its type
        TODO Implement other types
    """
    dtpo_log('info', 'get_file_type for %s - needs fully implementing',
             source_file)

    return k.PDF_Document, 'application/pdf'