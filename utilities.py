#!/usr/bin/python    #pylint: disable-msg=C0103
"""
Class which holds the base config class and utility functions
"""

import re
import os

from datetime import date
import logging

import gntp.notifier

from dtpoexceptions import DTPOFileError, ParseError

#
#    Method to check whether a directory is accessible
#
def check_directory_permissions(directory) :
    """ Checks whether the specified directory is accessible
    """

    return_string = False

    test_file = directory + "/testFile.Remove"

    try :
        file_pointer = open(test_file, "w")
        file_pointer.write("TEST")
        file_pointer.close()
        os.remove(test_file)
    except IOError as io_error:
        return_string = "directory not accessible. Error -> '%s'" % (
            str(io_error) )

    return return_string


class Config (object) :                               #pylint: disable-msg=R0903
    """ Config class contains the primary arributes needed to parse a file
        This must be created
    """

    debug = False
    logger = None
    config = None

    def __init__(self, config_file) :

        # These are set in the global scope but for testing purposes
        # we reset every time
        Config.debug = None
        Config.logger = None
        Config.growl = None

        #    Set up an array to make it easy to parse
        self.debug_setting = { 'value' : False, 'set' : True, 'type' : 'na' }
        self.source_dir = { 'value' : '', 'set' : False, 'type' : 'dir' }
        self.devonthink_database_dir = { 'value' : '', 'set' : False,
            'type' : 'dir' }
        self.orphan_docs_dir = { 'value' : '', 'set' : False, 'type' : 'dir' }
        self.log_dir = { 'value' : '', 'set' : False, 'type' : 'dir' }
        self.pattern_file = { 'value' : '', 'set' : False, 'type' : 'file' }
        self.working_directory = { 'value' : '', 'set' : False, 'type' : 'dir' }
        self.trash_directory = { 'value' : '', 'set' : False, 'type' : 'dir' }

        self.parameters = {
            'DEBUG' : self.debug_setting,
            'SOURCE_DIRECTORY' : self.source_dir,
            'DEVONTHINK_DATABASES_DIRECTORY' : self.devonthink_database_dir,
            'ORPHAN_DOCUMENTS_DIRECTORY' : self.orphan_docs_dir,
            'LOG_DIRECTORY' : self.log_dir    ,
            'PATTERN_FILE' : self.pattern_file,
            'WORKING_DIRECTORY' : self.working_directory,
            'TRASH_DIRECTORY' : self.trash_directory
        }
        Config.config = self

        #
        #    Now read through the file and set the parameters
        #
        if Config.debug :
            print "Config File init -> " + config_file

        line_number = 0
        try :
            for line in open(config_file) :
                line_number += 1
                #    Change this pattern carefully!!!
                search = re.match('(^[^#].*)=(.[^#]*)', line.lstrip())

                # if we found something then
                if (search) :
                    key = search.group(1)
                    value = search.group(2).rstrip()

                    if Config.logger :
                        dtpo_log('debug', "key -> '%s', value -> '%s'",
                            key, value)

                    if key in self.parameters :
                        #
                        #    Check if it's already been set
                        #
                        if key != "DEBUG" and self.parameters[key]['set'] :
                            error_message = "Duplicate key -> '{0}', now -> '" \
                                "{1}', was -> '{2}'".format(key, value,
                                self.parameters[key]['value']) +"'"
                            dtpo_log('error', error_message)
                            raise DTPOFileError(config_file, line_number,
                                error_message)
                        #
                        #    Check for empty attribute
                        #
                        if value == "" :
                            error_message = "Missing value for key -> '{0}'" \
                                .format(key)
                            if (Config.logger) :
                                dtpo_log('error', error_message)
                            raise DTPOFileError(
                                config_file, line_number, error_message)
                        self.parameters[key]['value'] = value
                        self.parameters[key]['set'] = True
                    else :
                        error_message = "Unexpected key -> '{0}', value -> "\
                            "'{1}'".format(key, value)
                        if Config.logger :
                            dtpo_log('error', error_message)
                        raise DTPOFileError(config_file, line_number,
                            error_message)


                    # Check for specials logging and debug

                    if (key == "LOG_DIRECTORY") :
                        #    Check whether the directory is accessible
                        return_string = check_directory_permissions(value)
                        if return_string :
                            error_message = "Log directory not accessible -> '"\
                                "{0}', error -> {1}".format(value,
                                return_string)
                            raise DTPOFileError(config_file, line_number,
                                                error_message)
                        set_up_logging(value)

                        self.valid_logging_methods = {
                            'debug' : self.logger.debug,
                            'error' : self.logger.error,
                            'info' : self.logger.info,
                            'warn' : self.logger.warn,
                            'fatal' : self.logger.fatal,
                        }

                    #
                    #    Debug only valid if Logger has been successfully
                    #    created
                    if (key == "DEBUG") :
                        if value == 'True' :
                            if not Config.logger :
                                raise DTPOFileError(config_file, line_number,
                                    "DEBUG enabled without LOG_DIRECTORY set")
                            Config.debug = True
                            Config.logger.setLevel(logging.DEBUG)
                            dtpo_log('debug', "debugging enabled in config " \
                                "'%s'", config_file)
            self.check_parameters_valid()

        except ParseError as parse_error :
            raise DTPOFileError (config_file, line_number, parse_error.message)

        except IOError as io_error :
            #    Failed to access the config file
            error_message = "Error accessing config file -> '{0}'" \
                .format(str(io_error))
            raise DTPOFileError (config_file, line_number, error_message)

    def check_parameters_valid(self) :
        """
        Now check that we have everything & that files/directories are
        accessible
        """
        for check_parameter in self.parameters :
            if (not self.parameters[check_parameter]['set']) :
                error_message = "Missing key -> '" + check_parameter + "'"
                if (Config.logger) :
                    dtpo_log('fatal', error_message)
                raise ParseError(error_message)

            if self.parameters[check_parameter]['type'] == 'dir' :
                value = self.parameters[check_parameter]['value']
                return_string = check_directory_permissions(value)
                if return_string :
                    error_message = "{0} not accessible " \
                        "-> {1}".format(
                            check_parameter,
                            return_string)
                    raise ParseError(error_message)
            elif self.parameters[check_parameter]['type'] == 'file' :
                value = self.parameters[check_parameter]['value']
                try :
                    file_pointer = open(value)
                    file_pointer.close()
                except IOError as io_error :
                    error_message = "File {0} not accessible -> {2}" \
                        .format(
                            check_parameter,
                            self.parameters[check_parameter]['value'],
                            str(io_error))
                    raise ParseError(error_message)

    def get_pattern_file(self) :
        """ Return PATTERN_FILE
        """
        return self.parameters['PATTERN_FILE']['value']

    def get_source_directory(self) :
        """ Return SOURCE_DIRECTORY
        """
        return self.parameters['SOURCE_DIRECTORY']['value']

    def get_working_directory(self) :
        """ Return WORKING_DIRECTORY
        """
        return self.parameters['WORKING_DIRECTORY']['value']

    def get_database_directory(self) :
        """ Return DEVONTHINK_DATABASES_DIRECTORY
        """
        return self.parameters['DEVONTHINK_DATABASES_DIRECTORY']['value']

    def get_orphan_directory(self) :
        """ Return ORPHAN_DOCUMENTS_DIRECTORY
        """
        return self.parameters['ORPHAN_DOCUMENTS_DIRECTORY']['value']

    def get_trash_directory(self) :
        """ Return TRASH_DIRECTORY
        """
        return self.parameters['TRASH_DIRECTORY']['value']

def orphan_file(file_to_orphan) :
    """  Move specified file to the orphan directory
         Generally used when a file can't be renamed or loaded
    """
    dtpo_log('debug', "orphan_file file -> %s", file_to_orphan)

    source = Config.config.get_source_directory() + '/' + file_to_orphan
    destination = \
        Config.config.get_orphan_directory() + '/' + file_to_orphan

    os.rename(source, destination)

def trash_file(file_to_trash, document_name) :
    """  Move specified file to the secure trash directory
         Generally used after a successful import
    """
    dtpo_log('debug', "trash_file file -> %s", file_to_trash)

    source = Config.config.get_source_directory() + '/' + file_to_trash
    destination = Config.config.get_trash_directory() + '/' + document_name

    os.rename(source, destination)

def dtpo_log(log_type, message_text, *args) :
    """
    Generate logging messages.  log_type is one of:
    debug, info, error, fatal.
    Note that this method will also work without Config being instatiated
    which makes it test safe
    """
    if Config.logger is not None:
        if log_type not in Config.config.valid_logging_methods :
            raise ValueError("Invalid logging type '{0}'".format(log_type))

        Config.config.valid_logging_methods[log_type](message_text, *args)

def dtpo_alert(log_type, reason = '', file_name = '', group_name = '') :
    """
    Generate growl alert messages.  log_type is one of:
    debug, info, error, fatal.
    Note that this method will also work without Config being instatiated
    which makes it test safe
    """
    if Config.growl is not None:
        if log_type not in Config.config.valid_logging_methods :
            raise ValueError("Invalid logging type '{0}'".format(log_type))

        if log_type != 'debug' :
            file_name = basename(file_name)
            if log_type == 'info' :
                sticky = False
                noteType = 'info'
                title = 'DTPO load success'
                description = '{0} to\n{1}'.format(file_name, group_name)
            elif log_type == 'error' :
                noteType = 'error'
                title = 'DTPO load failure'
                sticky = True
                description = '{0}\n{1} orphaned'.format(reason, file_name)
            elif log_type == 'warn' :
                noteType = 'info'
                sticky = True
                title = 'DTPO load warning'
                description = '{0} {1}'.format(reason, file_name)
            else :
                noteType = 'error'
                title = 'DTPO system error'
                sticky = True
                description = '{0}\nfile {1} not processed'.format(
                    reason, file_name)

            Config.growl.notify(
                noteType = noteType,
                title = title,
                description = description,
                icon='http://www.devontechnologies.com/typo3temp/pics/' \
                     'e9b5034330.png',
                sticky = sticky,
                priority = 1)

def set_up_logging(log_directory) :
    """
        Initialise logging
    """
    logging.basicConfig (
        filename = log_directory + '/' + \
            date.today().strftime('%y-%m-%d') + \
            ".dtpo_autoload.log",
        format = "%(levelname)-10s %(asctime)s %(message)s",
        level = logging.INFO)
    Config.logger = logging.getLogger('dtpo_autoload')

    # Now set up the Growl notification
    Config.growl = gntp.notifier.GrowlNotifier(
        applicationName = 'DTPO Autoload',
        notifications = ['info','error'],
        defaultNotifications = ['info'])
    Config.growl.register()

def basename(source_file) :
    """
	Extract the basename of the file
	"""
    if source_file is not None and source_file != '' :
        return os.path.basename(source_file)

    return ''