#!/usr/bin/python    #pylint: disable-msg=C0103
"""
    Method called to validate that a pattern_spec is what is expected
    WARNING - Makes heavy use of evaluated strings so not necesaarily the
    easiest to understand - but seems to be the most efficient way
    to specify it
"""

from dtpoparsespec import DTPOParseSpec   #pylint: disable-msg=F0401

def check_method(pattern_spec) :
    """
    Check function for DTPOParseSpec
    """
    assert pattern_spec

    defaults = [
        ('default_group', 'Inbox'),
        ('default_database', 'Home Filing'),
        ('default_tags', 'Action Required')
    ]

    file_patterns = []

    entry1 = (
        ('value', 'database', 'Home Filing'),
        ('value', 'group', 'Finance/First Direct/Statements/Sole'),
        ('value', 'tags', ''),
        ('value', 'description', 'First Direct Sole Account'),
        ('pattern', 'string1_details', ( 'first direct internet banking - " \
            "Statement', 'First Direct Sole Statement', 0)),
        ('pattern', 'string2_details', ()),
        ('pattern', 'date_details', ( 'Statement Date', \
            '[0-9][0-9] [a-zA-Z][a-zA-Z][a-zA-Z] [0-9][0-9]', 2))
    )
    file_patterns.append(entry1)

    #    Validate the defaults
    #    this is messy as its evaluating strings - be careful changing

    error_message = ""

    for check_details in defaults :
        check_val = eval ('file_pattern.' + check_details[0])
        check_string = check_val + ' == ' + check_details[1]
        check = eval(check_string)

        if not check :
            error_message = "Pattern check - bad default.  Got -> '" \
                   + check_val + "', expected '" + check_details[1]
            return error_message

    #    Done the defaults now do the main event
    #    First check that the pattern lists are the same length
    if not file_patterns.count() == pattern_spec.file_patterns.count() :
        error_message = "Pattern check - incorrect number of patterns.  Got " \
            "-> {0}, expected {1}".format(pattern_spec.file_patterns.count(),
                                          file_patterns.count())
    # Now iterate through the list
    counter = 0
    for pattern_to_check in pattern_spec.file_patterns :
        details = file_patterns[counter]

        for check_details in details :
            #
            #    Action depends on whether it's a straight value or a pattern
            #    tuple
            if check_details[0] == 'value' :
                pattern_to_check_parameter = check_details[1]
                pattern_to_check_value = eval(
                    'pattern_to_check.' + pattern_to_check_parameter)

                check_value = check_details[2]

                check_string = "pattern_to_check.{0} == '{1}".format(
                    check_details, check_value)

                if not eval(check_string) :
                    error_message = "Pattern check - bad entry in pattern {0}" \
                        " for attribute {1}, Got -> '{2}', expected '{3}" \
                        .format(counter, check_parameter, )


