#!/usr/bin/python

#
#	default check Function for Config File testing - This should never be called
#

from dtpoparsespec import DTPOParseSpec #pylint:disable-msg=W0611

def check_method(pattern_spec) :
	print "TEST FAILED - Method should not be called"
	return False
