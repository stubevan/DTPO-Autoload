#!/usr/bin/python                     #pylint: disable-msg=C0103
"""
    Script which will take a list of files from the command line and attempt
    to upload them into DevonThink
"""

import os
import optparse

from utilities import Config, pop_up_alert, orphan_file, dtpo_log, basename
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
        print file_error.message
    except ParseError as parse_error :
        pop_up_alert("DTPO Initialsation failed.  Files not orphaned.  ->"\
            " " + parse_error.message)
        raise SystemExit("FATAL ERROR Config File not specified")

    #
    #    Now iterate through the files
    #
    for source_file in source_file_args:
        dtpo_log('debug', "Started processing -> %s", source_file)

        try :
            #
            #    Convert the file to text if we can and then parse it
            #
            import_details = get_import_parameters(source_file, pattern_spec)
            if opts.test_parse :
                import_details.print_import_details(source_file)
            else :
                execute_import(import_details)
        except DTPOFileError as file_error :
            print file_error.message
        except ParseError as parse_error :
            #
            #    We failed ... Move the file to the Orphan directory
            #
            print parse_error.message
            dtpo_log('error', "Import failed for '%s' - orphaning file",
                basename(source_file))
            orphan_file(source_file)


if __name__ == '__main__':
    main()

#TODO check that input file is passed alone