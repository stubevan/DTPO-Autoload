#!/usr/bin/python                                     #pylint: disable-msg=C0103
"""
    Method called to validate that a pattern_spec is what is expected
    WARNING - Makes heavy use of evaluated strings so not necesaarily the
    easiest to understand - but seems to be the most efficient way
    to specify it
"""

from dtpoparsespec import SearchDetails, DTPOParseSpec #pylint:disable-msg=W0611


def check_method(pattern_spec) :
    """
    Check function for DTPOParseSpec
    """
    assert pattern_spec

    defaults = [
        ('default_group', 'Default Group'),
        ('default_database', 'Default Database'),
        ('default_tag', 'Default Tag')
    ]

    file_patterns = []

    entry = (
        ('value', 'database', 'Default Database'),
        ('value', 'group', 'Default Group'),
        ('value', 'tag', 'Default Tag'),
        ('value', 'description', ''),
        ('pattern', 'string1_pattern', ('Pattern 1 key', None, 0)),
        ('pattern', 'string2_pattern', ()),
        ('pattern', 'date_pattern', ( 'Date 1 key', 'Date 1 value', 2))
    )
    file_patterns.append(entry)

    entry = (
        ('value', 'database', 'Default Database'),
        ('value', 'group', 'Default Group'),
        ('value', 'tag', 'Default Tag'),
        ('value', 'description', ''),
        ('pattern', 'string1_pattern', ('Pattern 2 key', 'Pattern 2 value', 0)),
        ('pattern', 'string2_pattern', ('Pattern2 key', 'Pattern2 value', 12)),
        ('pattern', 'date_pattern', ( 'Date 2 key', 'Date 2 value', -22))
    )
    file_patterns.append(entry)

    #    Validate the defaults
    #    this is messy as its evaluating strings - be careful changing
    for check_details in defaults :
        check_val = eval("pattern_spec." + check_details[0])
        check_string = 'pattern_spec.' + check_details[0] + ' == "' + \
            check_details[1] + '"'
        check = eval(check_string)

        if not check :
            print "Pattern check - bad value for {0}.  Got -> " \
                "'{1}', expected '{2}'".format(check_details[0],
                                               check_val, check_details[1])
            return False

    #    Done the defaults now do the main event
    #    First check that the pattern lists are the same length
    if not len(file_patterns) == len(pattern_spec.file_pattern_list) :
        print "Pattern check - incorrect number of patterns.  Got " \
            "-> {0}, expected {1}".format(len(pattern_spec.file_pattern_list),
                                          len(file_patterns.count))
        return False

    # Now iterate through the list
    counter = 0
    for pattern_to_check in pattern_spec.file_pattern_list :
        details = file_patterns[counter]

        for check_details in details :
            check_parameter = check_details[1]
            check_value = check_details[2]

            #
            #    Action depends on whether it's a straight value or a pattern
            #    tuple
            if check_details[0] == 'value' :

                pattern_value = eval('pattern_to_check.' + check_parameter)

                check_string = "pattern_value == '{1}'".format(
                    check_parameter, check_value)

                if not eval(check_string) :
                    print "Pattern check - bad entry in pattern {0} " \
                        " for attribute {1}, Got -> '{2}', expected '{3}'" \
                        .format(counter, check_parameter,
                                pattern_value, check_value)
                    return False
            #
            #    Now check the patterns
            else :
                pattern_details = eval("pattern_to_check." + check_parameter)
                if len(check_value) == 0 :
                    if pattern_details :
                        print 'Pattern check - bad entry in pattern {0} ' \
                            'Search Details {1} should be empty'.format(
                            counter, check_parameter)
                        return False
                else :
                    #
                    # nothing to check = check that sent value also 0
                    check_pattern = SearchDetails(
                        key_pattern = check_value[0],
                        value_pattern = check_value[1],
                        offset_line = check_value[2])

                    error_check = (check_pattern != pattern_details)
                    if error_check :
                        print "Pattern check - bad entry in pattern {0} " \
                            "for attribute {1}, {2}".format(counter,
                                                            check_parameter,
                                                            error_check)
                        return False
        counter = counter + 1
    return True
