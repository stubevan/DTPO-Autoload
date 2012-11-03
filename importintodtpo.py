#!/usr/bin/env python

import logging
from dtpoimportparameters import *
from utilities import *
import sys
from pdfminer.pdfparser import PDFDocument, PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter, process_pdf
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from appscript import *
from datetime import *


#
#   Parse the PDF and return as an array
#
def parsePDF(sourceFile) :
    
    Config.logger.info("parsePDF sourceFile -> '%s'", sourceFile)
    # input option
    password = ''
    pagenos = set()
    maxpages = 0
    # output option
    outfile = None
    outtype = None
    outdir = None
    layoutmode = 'normal'
    codec = 'utf-8'
    pageno = 1
    scale = 1
    caching = True
    showpageno = True
    laparams = LAParams()
    #
    PDFDocument.debug = debug
    PDFParser.debug = debug
    CMapDB.debug = debug
    PDFResourceManager.debug = debug
    PDFPageInterpreter.debug = debug
    PDFDevice.debug = debug
    #
    rsrcmgr = PDFResourceManager(caching=caching)
    infile = config.getSourceDirectory() + "/" + sourceFile
    outfile = config.getWorkingDirectory() + "/" + sourceFile + ".txt"

    outtype = 'text'
    outfp = file(outfile, 'w')
    fp = file(fname, 'rb')
    device = TextConverter(rsrcmgr, outfp, codec=codec, laparams=laparams)
    process_pdf(rsrcmgr, device, fp, pagenos, maxpages=maxpages, password=password,
                    caching=caching, check_extractable=True)
    fp.close()
    device.close()
    outfp.close()
    
    #   Got the PDF converted = now get it into an array
    fileArray = []
    for line in open(outfile) :
        fileArray.append(line)
        
    return fileArray
    

#
#   Parameters required for an import
class DTPOImportParameters (object) :
    
    def __init__(self, string1SearchResults, string2SearchResults, dtpoImportParameters) :
    
        self.database = dtpoImportParameters.getDefaultDatabase()
        self.group = dtpoImportParameters.getDefaultGroup()
        self.documentName = dtpoImportParameters.getDocumentName()
        self.tags = dtpoImportParameters.getDefaultTags()

        if (searchString1Results) :
            self.database = searchString1Results.getDatabase()
            self.group = searchString1Results.getGroup()
            self.tags = searchString1Results.getTags()


            # Now construct the document Name = which could end up being a default
            self.documentName = searchString1Results.getTarget()
            if (dateSearchResults) :
                self.documentName = dateSearchResults.getTarget() + " " + self.documentName
            if (string2SearchResults) :
                self.documentName = self.documentName + string2SearchResults.getTarget()
                
#
#   Got a line - lets see of we can find a match   
def searchForMatch (line, lineNumber, searchStringParameters) :
   
    searchStringResults = SearchStringResults()
    
    #
    #   Iterate through the pattern List
    for huntPattern in searchStringParameters.getPatternList() :
       
        Config.logger.debug("--> hunting for -> '%s'", huntPattern)
        hunt = match(huntPattern, line)
        if (hunt) :
            #
            #   We've got a match
            #
            Config.logger.info("line %04d, found match for -> '%s' in -> '%s'", line, huntPattern, line)    #
            #   Now determine what to do - if no subsidary hunt of match is set then we have what what we want
            #
            targetDetails = searchStringParameters.getTargetDetails(huntPattern)
            targetPattern = targetDetails.getTargetPattern()
            if not (targetPattern) :
                #
                #   No further target string has been set so the required results will be in the match
                #
                searchStringResults.targetString = hunt.group(1)
                searchStringResults.offsetLine = targetDetails.getOffsetLine()
    
    return searchStringResults
 
                        
                        
#   Function which iterates through an array and extracts the relevant details for the Import
def parseFile(fileLines, dtpoParseSpec, config) :
    #
    #   Now iterate through the file and see if we can find anything
    #
    lineNumber = 1
    lineBuffer = []
    
    for line in fileLines :
        
        Config.logger.debug("line %04d -> %s", lineNumber, line)
        
        lineBuffer[line] = line
        
        #
        #   We are still on the initial hunt
        #
        if not (searchString1Results) :
            for filePattern in dtpoParseSpec.getFilePatterns():
                searchString1Results = searchForMatch(line, lineNumber, filePattern.getstring1Pattern())
                if (searchString1Results) :
                    break
            
        if (searchString1Results) :
            #
            #   We have the main string - now look for the date if we don't have it
            if not (searchDateResults) :
                searchDateResults = searchForMatch(line,
                                                   lineNumber,
                                                   searchString1Results.getDateSearchParameters())
                
            #   See if we need to be looking for String 2
            if (not string2SearchParameters and searchString1Results.getSearchString2Parameters()) :
                searchString2Results = searchForMatch(line, lineNumber, string2SearchParameters)
                    
        #
        #   We've done with the main matching - we now need to see if there are forward looking searches outstanding
        #   search Line will update the results object
        #
        if (searchString1Results and searchString1Results.seekForward() == lineNumber) :
            earchLine(line, searchString1Results)
                
        if (searchString2Results and searchString2Results.seekForward() == lineNumber) :
            searchLine(line, searchString2Results)
                
        if (searchString2Results and searchString2Results.seekForward() == lineNumber) :
            searchLine(line, searchDateResults)
            
        lineNumber = lineNumber + 1
        
    #   We're done processing the file
    #   Construct the  return class
    dtpoImportParameters = DTPOImportParameters(string1SearchResults, string2SearchResults, dateSearchResults, config)
    return dtpoImportParameters

#
#   Determine the file type
#   Function not completed always sets to PDF |TODO
def getFileType(sourceFile, fileType, mimeType) :
    fileType = k.PDF_document,
    mimeType = 'application/pdf'
#
#   Now run the actual import into DTPO
def executeImport(sourceFile, dtpoImportParameters, config) :
    
    Config.logger.info("executeImport sourceFile -> %s", sourceFile)
    Config.logger.info("executeImport database -> %s", dtpoImportParameters.database)
    Config.logger.info("executeImport group -> %s", dtpoImportParameters.group)
    Config.logger.info("executeImport tags -> %s", dtpoImportParameters.tags)
    Config.logger.info("executeImport documentName -> %s", dtpoImportParameters.documentName)    
    
    dtpodb = app(u'DEVONthink Pro').open_database(dtpoImportParameters.database)
    dtpodbid = dtpodbid

    dtpogroup = app(u'DEVONthink Pro').create_location(dtpoImportParameters.group, in_=app.databases.ID(dtpodbif))
    dtpogroupid = dtpogroup.id()

    fileType = ""
    mimeTypeType = k.Unknown
    
    getFileType(sourceFile, fileType, mimeType)
    
    doc = app(u'DEVONthink Pro').create_record_with({
        k.name: dtpoImportParameters.documentName,
        k.tags: dtpoImportParameters.tags,
        k.path: sourceFile,
        k.MIME_type: mimeType,
        k.type: ftpoFileType}, in_=app.databases.ID(dtpoid).parents.ID(dtpogroupod))
    
    docid = dic.id()

    app(u'DEVONthink Pro').databases.ID(dtpoid).contents.ID(docid).unread.set(True)


def importFileIntoDTPO(sourceFile, dtpoParseSpec, config) :
    
    success = False
    
    Config.logger.info("importFilesIntoDTPO sourceFile -> %s", sourceFile)
    
    #
    #   parse the PDF and turn it into a list
    #
    fileLines = parsePDF(sourceFile)
    
    #   Parse the file and then do the import
    dtpoImportParameters = parseFile(fileLines, dtpoParseSpec, config)
    
    success = executeImport(sourceFile, dtpoImportParameters, config)
    
    return success
    

