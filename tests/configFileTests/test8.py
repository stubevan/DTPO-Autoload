#!/usr/bin/python

from utilities import *

#
#	Check function Config File testing
#	Note that this is based on the contents of the config file configfile_test8
#

def check_method() :
	
	success = True
	
	debugSetting = { 'value' : False, 'set' : True }
	sourceDirectory = { 'value' : '/Volumes/Encrypted Docs/Time For Action', 'set' : False }
	devonThinkDatabaseDirectory = { 'value' : '/Volumes/Encrypted Docs/Devon Filing', 'set' : False }
	orphanDocumentsDirectory = { 'value' : '/Volumes/Encrypted Docs/Time For Action/Orphan Documents', 'set' : False }
	logDirectory = { 'value' : '/Volumes/App Data/Script Logs', 'set' : False }
	patternFile = { 'value' : '/Users/stu/Development/scripts/dtpo_autoload/dtpo_autoload_patterns.conf', 'set' : False }
	working_directory = { 'value' : '/Volumes/App Data/Working Area', 'set' : False }
	
	parameters = { 
		'DEBUG' : debugSetting,
		'SOURCE_DIRECTORY' : sourceDirectory,
		'DEVONTHINK_DATABASES_DIRECTORY' : devonThinkDatabaseDirectory,
		'ORPHAN_DOCUMENTS_DIRECTORY' : orphanDocumentsDirectory,
		'LOG_DIRECTORY' : logDirectory,
		'PATTERN_FILE' : patternFile,
		'WORKING_DIRECTORY' : working_directory
	}
	
	#
	#	Iterate through the config parameters to make sure they are all set
	for key in Config.config.parameters :
		if key in parameters :
			if str(parameters[key]['value']) == str(Config.config.parameters[key]['value']) :
				parameters[key]['set'] = True
			else :
				print "TEST FAILED Value for key -> '" + key + "' not set correctly"
				print "Expected -> '" + str(parameters[key]['value']) + "'"
				print "Got      -> '" + str(Config.config.parameters[key]['value']) + "'"
		else :
			print "TEST FAILED Unexpected key in Config.config.parameters -> '" + key + "'"
			success = False
	
	#
	#	Now iterate through the validation keys to make sure they have all been set
	for key in parameters :
		if not parameters[key]['set'] :
			print "TEST FAILED - parameter with key -> '" + key + "' has not been set"
			
	
	return success
