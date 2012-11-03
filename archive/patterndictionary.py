#!/usr/bin/env pythonw
# -*- coding: utf-8 -*-

#	Holds the patterms detailing how to search files
#	Goal is a filed document with the name YYYY-MM-DD {Pattern 1} {Pattern 2}.type
#	DefaultTag::Action Required		-- Optional Can specify a tag to add to each document
#	DefaultGroup::Inbox			-- Mandatory
#
#	Database::Home Filing
#	Description::First Direct Sole Account	-- Comment [Optional]
#	Group::Finance/First Direct/Statements/Sole	-- Group Hierarchy
#	Pattern1::first direct internet banking - Statement->(+/- lines)First Direct Sole Statement
#		-- Regular express to look for followed by optional target which specifes end pattern
#		-- If no target is specifed then the results of the first pattern become the target
#	Patter2:: .... as Pattern 1
#	Date:: as Pattern 1
#    
    
from re import *
from datetime import date
import logging
from utilities import *


class PatternDictionary (object) :
	
	def __init__(self, patternFile) :
	
		#
		#	Now read through the file and set the parameters
		#
		Config.logger.info("PatternDictionary file -> %s ", patternFile)
		
		self.defaultGroup = False
		self.defaultTag = False
		
		#
		#	patterns are held as an array (which is ok - we have to iterate through anyway)
		self.patternDictionary = {}
