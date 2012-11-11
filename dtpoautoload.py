#!/usr/bin/python                     #pylint: disable-msg=C0103
"""
    Script which will take a list of files from the command line and attempt
    to upload them into DevonThink
"""

import optparse
import os

from utilities import Config, dtpo_alert, orphan_file, dtpo_log, basename, \
    trash_file
from dtpoexceptions import ParseError
from dtpoparsespec import DTPOParseSpec, DTPOFileError
from importintodtpo import execute_import, get_import_parameters

def main() :
    """
    Get the command line arguments
    """
    p = optparse.OptionParser()
    p.add_option("-d", action="store_true", dest="debug")
    p.add_option("--debug", action="store_true", dest="debug")
    p.add_option("--config_file", action="store", dest="config_file")
    p.add_option("--test_parse", action="store_true", dest="test_parse")
    p.set_defaults(debug = False)

    opts, source_file_args = p.parse_args()

    try :
        # Config File is mandatory
        if not opts.config_file :
            raise ParseError("No Config file")
        #
        #    Upload the configs
        #
        Config(opts.config_file)
        pattern_spec = DTPOParseSpec(Config.config.get_pattern_file())
    except DTPOFileError as file_error:
        dtpo_alert(log_type = 'fatal', reason = file_error.message)
        raise SystemExit("FATAL ERROR - Failed to parse config file")
    except ParseError as parse_error :
        dtpo_alert('fatal', reason = parse_error.message)
        raise SystemExit("FATAL ERROR - Failed to parse pattern file")

    #
    #    Now iterate through the files
    #
    for source_file in source_file_args:
        dtpo_log('info', "Started processing -> %s", source_file)

        try :

            #  TODO - we're assuming PDF files here
            #  Check that the file name actually ends in
            #  pdf if not rename it as it will save trouble with DTPO later
            suffix = source_file[-3:]
            if suffix.lower() != 'pdf' :
                dtpo_log('debug', "Adding pdf suffix on to '%s'",
                         source_file)
                source_dir = Config.config.get_source_directory() + '/'
                os.rename(source_dir + source_file,
                          source_dir + source_file + '.pdf')
                source_file += '.pdf'
            #
            #    Convert the file to text if we can and then parse it
            #
            import_details = get_import_parameters(source_file, pattern_spec,
                                                   opts.test_parse)
            if opts.test_parse :
                import_details.print_import_details(source_file)
            else :
                execute_import(import_details)
                trash_file(source_file, import_details.get_document_name())
                dtpo_alert('info',
                           file_name = import_details.get_document_name(),
                           group_name = import_details.group)
        except DTPOFileError as file_error :
            #    We failed ... Leave the file be as there is a problem with it
            dtpo_log('error', "Import failed for '%s' - file not touched\n%s",
                basename(source_file), file_error.message)
            dtpo_alert('fatal', reason = file_error.message,
                       file_name = source_file)

        except ParseError as parse_error :
            #    We failed ... Move the file to the Orphan directory
            dtpo_log('error', "Import failed for '%s' - orphaning file\n%s",
                basename(source_file), parse_error.message)
            dtpo_alert('error', reason = parse_error.message,
                       file_name = source_file)
            orphan_file(source_file)
        except Exception as exception :
            #   Something horrible has happend
            dtpo_log('fatal', "System error for '%s'\n%s",
                     basename(source_file), str(exception))
            dtpo_alert('fatal', reason = str(exception),
                       file_name = source_file)

        dtpo_log('debug', 'Completed Successfully')


if __name__ == '__main__':
    main()

#TODO check that input file is passed alone