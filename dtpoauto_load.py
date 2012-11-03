#!/usr/bin/env pythonw
# -*- coding: utf-8 -*-
#
# Script which will take a list of files from the command line and attempt
# to upload them into DevonThink
#

import sys
import optparse
import logging

from utilities import *
from patterndictionary import *
from importintodtpo import *
from dtpoimportparameters import *


#	Get the command line arguments
p=optparse.OptionParser()
p.add_option("-d", action="store_true", dest="debug")
p.add_option("--debug", action="store_true", dest="debug")
p.add_option("--config_file", action="store", dest="configFile")
p.set_defaults(debug=False)


opts, sourceFileArgs = p.parse_args()

#	Config File is mandatory
if (not opts.configFile) :
	raise SystemExit("FATAL ERROR Config File not specified")

#
#	Upload the configs
#
config = Config(opts.configFile)

dictionary = PatternDictionary(config.getPatternFile())

#
#	Now iterate through the files
#
for sourceFile in sourceFileArgs:
	Config.logger.info("Started processing -> %s", sourceFile)

	#
	#	Convert the file to text if we can and then parse it
	#
	dtpoParseSpec = DTPOParseSpec(sourceFile, config)

	if not (dtpoParseSpec.result() and importFileIntoDTPO(sourceFile, dtpoParseSpec, config)) :
		#
		#	We failed ... Move the file to the Orphan directory
		#
		Config.logger.error("Import Failed - orphaning file")
		popUpAlert("Failed to import file " + sourceFile + ".  File Orphaned")
#		orphanFile(sourceFile, config)

