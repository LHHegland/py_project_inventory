''' Initialize logging to file or stderr (e.g. info, debug, warning, error, critical).

PURPOSE: Provide helpful information for testing and debugging.

USAGE: 
  - Command Line Interface: py logz.py --h
  - Import: 
            ~~~
            import lib.utils.logz
            mylog = lib.utils.logz.setup().getChild('module_name') # Log to stderr; see function usage notes.
            # OR
            import lib.utils.logz
            logpath = 'path_to_log_directory'
            mylog = lib.utils.logz.init_logfile(logpath, __file__).getChild('module_name')
            
            [ … other imports and definitions … ]

            if __name__ == '__main__':            
                try: # Code to execute, at least until an exception occurs
                    mylog.info('Trying Actions…')
                    
                    # … module code to execute, at least until an exception occurs …
                    
                    # … user messages as needed …
                    print('🖐 Message to user.')
                    mylog.debug('Message.')
                    mylog.info('Message')
                    mylog.warning('Message.')
                    mylog.error('Message.')
                    mylog.critical('Message.')
                    
                    mylog.info('🟩 …Completed Actions.')
                # … optional code to handle specified exceptions …
                except Exception: # Code to handle unspecified exceptions
                    mylog.exception('🟥 FATAL ERROR: UNEXPECTED EXCEPTION OCCURRED!')
                finally: # Code to always execute, even if an exception occurs
                    lib.utils.logz.term_logfile(mylog, __file__)
            ~~~

REFERENCES:
  - Python → Documentation
      - HOWTO: Logging
          - Basic Logging Tutorial -- https://docs.python.org/3/howto/logging.html
          - Advanced Logging Tutorial -- https://docs.python.org/3/howto/logging.html#logging-advanced-tutorial
          - Logging Cookbook -- https://docs.python.org/3/howto/logging-cookbook.html
      - The Python Standard Library
          - logging
              - Logging -- https://docs.python.org/3/library/logging.html
              - .config — configuration -- https://docs.python.org/3/library/logging.config.html
              - .handlers — handlers -- https://docs.python.org/3/library/logging.handlers.html
          - argparse -- command line use only, not required for import use -- https://docs.python.org/3/library/argparse.html
          - datetime -- https://docs.python.org/3/library/datetime.html
          - os -- https://docs.python.org/3/library/os.html
          - platform -- https://docs.python.org/3/library/platform.html
'''
import argparse
import datetime
import logging
import os
import platform


def get_cli_help():
    ''' Initialize command line interface help messaging

    USAGE: py logz.py --h

    REFERENCES:
      - argparse -- used for command line only, not required for import use.
                    See https://docs.python.org/3/library/argparse.html
    '''
    parser = argparse.ArgumentParser(
        prog='logz',
        description='Initialize logging to file or stderr'
                    ' (e.g. info, debug, warning, error,'
                    'critical).',
        epilog='For questions or concerns, please '
             + 'contact lance.hegland@civic-innovations.com'
    )
    parser.add_argument('--lp', '--logpath',
                        action='store', default='', type=str, required=False, dest='logpath',
                        help='for log type 2: path to logfile (e.g. D:\\path\\)'
    )
    parser.add_argument('--lpfn', '--logpathfilename',
                        action='store',  default='output.log', type=str, required=False, dest='logpathfilename',
                        help='for log type 3: path and file name for logfile (e.g. D:\\path\\to\\filename.log)'
    )
    parser.add_argument('--tes', '--testexceptionspecified',
                        action='store_true', dest='is_test_exception_specified',
                        help='optional flag to test specified exception handling'
    )
    parser.add_argument('--teu', '--testexceptionunspecified',
                        action='store_true', dest='is_test_exception_unspecified',
                        help='optional flag to test unspecified exception handling'
    )
    parser.add_argument('logtype',
                        action='store', nargs=1, default=1, type=str, choices=['1', '2', '3'],
                        help='log output to... 1 = screen, 2 = logpath (see --logpath), or 3 = logpathfile (see --logpathfilename)'
    )
    return parser.parse_args()


def setup(logfile_path_name: str | None = None) -> logging.Logger:
    ''' Initialize logging to file or stderr (e.g. info, debug, warning, error, critical).

    PURPOSE: Store or display helpful log record messages for testing and debugging.

    USAGE:
        ~~~
        import lib.utils.logz
        mylog = lib.utils.logz.setup().getChild('module_name') # to stderr
        # OR
        logpathfilename = 'path\\to\\filename.log'
        lib.utils.logz.setup(logpathfilename).getChild('module_name') # to path\to\filename.log

        [ … other imports and definitions … ]

        if __name__ == '__main__':
            try: # Code to execute, at least until an exception occurs
                mylog.info('Trying Actions…')
                
                # … module code to execute, at least until an exception occurs …
                
                # … user messages as needed …
                print('🖐 Message to user.')
                mylog.debug('Message.')
                mylog.info('Message')
                mylog.warning('Message.')
                mylog.error('Message.')
                mylog.critical('Message.')
                
                mylog.info('🟩 …Completed Actions.')
            # … optional code to handle specified exceptions …
            except Exception: # Code to handle unspecified exceptions
                mylog.exception('🟥 FATAL ERROR: UNEXPECTED EXCEPTION OCCURRED!')
        ~~~
    INPUT:
      - logfile_path_name (str)(optional) = path and name of log file, if omitted stream to stderr
                                            (e.g. D:\\path\\name.log)

    OUTPUT:
      - mylog (logging.Logger) = logger instance
    '''
    # Define filter functions
    def filter_fyi(record: logging.LogRecord) -> bool:
        '''
        Filter to accept log records with level less than warning level, otherwise ignore.

        USAGE: 
        - handler.addFilter(filter_fyi)

        INPUT:
        - record (logging.LogRecord) = log record instance -- see https://docs.python.org/3/library/logging.html#logging.LogRecord

        OUTPUT:
        - (bool) = true to accept, false to ignore
        '''
        return record.levelno < 30 # logging.WARNING value
    

    def filter_alert(record: logging.LogRecord) -> bool:
        '''
        Filter to accept log records with level greater than or equal to warning level, otherwise ignore.

        USAGE: 
        - handler.addFilter(filter_alert)

        INPUT:
        - record (logging.LogRecord) = log record instance -- see https://docs.python.org/3/library/logging.html#logging.LogRecord

        OUTPUT:
        - (bool) = true to accept, false to ignore
        '''
        # Because child handlers do not check message level, do it here:
        # See https://www.electricmonk.nl/log/2017/08/06/understanding-pythons-logging-module/
        return record.levelno >= 30 # logging.WARNING value
    

    def filter_add_cntxt(record: logging.LogRecord) -> bool:
        ''' Filter to add contextual color character flag (cntxt_flag) to LogRecord (e.g. ⚪, ⬛, 🟧, 🟥, 🟥🟥)

        USAGE: 
        - logger.addFilter(filter_add_cntxt)

        INPUT:
        - record (logging.LogRecord) = log record instance -- see https://docs.python.org/3/library/logging.html#logging.LogRecord

        OUTPUT:
        - (bool) = true to accept all records
        '''
        match record.levelname:
            case 'DEBUG':
                record.cntxt_flag = '⚪'
            case 'INFO':
                record.cntxt_flag = '⬛'
            case 'WARNING':
                record.cntxt_flag = '🟧'
            case 'ERROR':
                record.cntxt_flag = '🟥'
            case 'CRITICAL':
                record.cntxt_flag = '🟥🟥'
            case _:
                record.cntxt_flag = ''
        
        return True # accept all records
        

    # Create logger instance for all log record messages.
    # See https://docs.python.org/3/howto/logging.html#logging-flow
    #     https://docs.python.org/3/howto/logging.html#loggers
    mylog = logging.getLogger() # Create logger instance.
    mylog.setLevel(logging.DEBUG) # Set logger level ≥ debug level.
    # No logger filter needed.

    # Create date format for all formatters.
    # See https://docs.python.org/3/library/time.html#time.strftime
    datefmt = '%Y-%m-%d %H:%M:%S %z'
    
    # Create different log record formats for various handler formatters.
    # See https://docs.python.org/3/library/logging.html#logrecord-attributes
    # For stderr, omit contextual color flag.
    fmt_stderr_fyi = (
        '\n'
        '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
    )
    fmt_stderr_alert = (
        '\n'
        '%(message)s \n'
        '%(asctime)s - %(name)s - %(levelname)s \n'
        '%(threadName)s → %(processName)s \n'
        '%(pathname)s \n'
        '→ %(module)s → %(funcName)s @ %(lineno)d \n'
        'EXCEPTION INFO: %(exc_info)s \n'
    )
    # For file, include contextual color flag.
    fmt_file_fyi = (
        '\n'
        '%(asctime)s - %(name)s - %(cntxt_flag)s %(levelname)s: %(message)s'
    )
    fmt_file_alert = (
        '\n'
        '%(cntxt_flag)s %(message)s \n'
        '%(asctime)s - %(name)s - %(levelname)s \n'
        '%(threadName)s → %(processName)s \n'
        '%(pathname)s \n'
        '→ %(module)s → %(funcName)s @ %(lineno)d \n'
        'EXCEPTION INFO: %(exc_info)s \n'
    )

    # Create formatters for handlers.
    # See https://docs.python.org/3/howto/logging.html#formatters
    formatter_stderr_fyi = logging.Formatter(fmt_stderr_fyi, datefmt)
    formatter_stderr_alert = logging.Formatter(fmt_stderr_alert, datefmt)
    
    formatter_file_fyi = logging.Formatter(fmt_file_fyi, datefmt)
    formatter_file_alert = logging.Formatter(fmt_file_alert, datefmt)

    if logfile_path_name == None: # Log all messages to stderr only.
        # Create logger handler to stderr for fyi messages (e.g. debug and info).
        # See https://docs.python.org/3/library/logging.handlers.html
        # See https://docs.python.org/3/library/logging.html#filter-objects
        handler_stderr_fyi = logging.StreamHandler() # Create handler.
        handler_stderr_fyi.setLevel(logging.DEBUG) # Set handler level ≥ debug level.
        handler_stderr_fyi.addFilter(filter_fyi) # Add handler filter: < warning level (i.e. only debug and info).
        handler_stderr_fyi.setFormatter(formatter_stderr_fyi) # Set handler formatter.
        mylog.addHandler(handler_stderr_fyi) # Add handler to logger instance.
        
    else: # Log all messages to logfile, plus alerts to stderr.
        # Create logger handler to logfile for fyi messages (e.g. debug and info).
        # See https://docs.python.org/3/library/logging.handlers.html
        # See https://docs.python.org/3/library/logging.html#filter-objects
        handler_file_fyi = logging.FileHandler(logfile_path_name, mode='a', encoding='utf-8') # Create handler.
        handler_file_fyi.setLevel(logging.DEBUG) # Set handler level.
        handler_file_fyi.addFilter(filter_fyi) # Add handler filter: allow only fyi messages (e.g. debug and info).
        handler_file_fyi.addFilter(filter_add_cntxt) # Add handler filter: add contextual color flag.
        handler_file_fyi.setFormatter(formatter_file_fyi) # Set handler formatter.
        mylog.addHandler(handler_file_fyi) # Add handler to logger instance.
       
        # Create logger handler to logfile for alert messages (e.g. warning, error, and critical).
        # See https://docs.python.org/3/library/logging.handlers.html
        # See https://docs.python.org/3/library/logging.html#filter-objects
        handler_file_alert = logging.FileHandler(logfile_path_name, mode='a', encoding='utf-8') # Create handler.
        handler_file_alert.setLevel(logging.WARNING) # Set handler level.
        handler_file_alert.addFilter(filter_alert) # Add handler filter: allow only alert messages (e.g. warning, error, and critical).
        handler_file_alert.addFilter(filter_add_cntxt) # Add handler filter: add contextual color flag.
        handler_file_alert.setFormatter(formatter_file_alert) # Set handler formatter.
        mylog.addHandler(handler_file_alert) # Add handler to logger instance.
    
    # Create logger handler to stderr for alert messages (e.g. warning, error, and critical).
    # See https://docs.python.org/3/library/logging.handlers.html
    # See https://docs.python.org/3/library/logging.html#filter-objects
    handler_stderr_alert = logging.StreamHandler() # Create handler.
    handler_stderr_alert.setLevel(logging.WARNING) # Set handler level ≥ warning level.
    handler_stderr_alert.addFilter(filter_alert) # Add handler filter: allow only alert messages (e.g. warning, error, and critical).
    handler_stderr_alert.setFormatter(formatter_stderr_alert) # Set handler formatter.
    mylog.addHandler(handler_stderr_alert) # Add handler to logger instance.

    # Return mylog instance.
    return mylog


def init_logfile(logpath: str, filepathname: str) -> logging.Logger:
    ''' Setup logging to file in logpath\\module_name-timestamp.log

    USAGE:
        ~~~
        import lib.utils.logz
        logpath = 'path_to_log_directory"
        mylog = lib.utils.logz.init_logfile(logpath, __file__).getChild('module_name')

        [ … other imports and definitions … ]

        if __name__ == '__main__':            
            try: # Code to execute, at least until an exception occurs
                mylog.info('Trying Actions…')
                
                # … module code to execute, at least until an exception occurs …
                
                # … user messages as needed …
                print('🖐 Message to user.')
                mylog.debug('Message.')
                mylog.info('Message')
                mylog.warning('Message.')
                mylog.error('Message.')
                mylog.critical('Message.')
                
                mylog.info('🟩 …Completed Actions.')
            # … optional code to handle specified exceptions …
            except Exception: # Code to handle unspecified exceptions
                mylog.exception('🟥 FATAL ERROR: UNEXPECTED EXCEPTION OCCURRED!')
            finally: # Code to always execute, even if an exception occurs
                lib.utils.logz.term_logfile(mylog, __file__)
        ~~~

    INPUT:
      - logpath (str) = path to directory for log file
      - modulefilepathname (str) = module file path and name (e.g. __file__)

    OUTPUT:
      - mylog (logging.Logger) = logger instance
    '''
    start_time = datetime.datetime.now()
    log_filename = logpath + os.path.basename(filepathname).split('.')[0] + '-' + start_time.strftime('%Y%m%d%H%M%S') + '.log'
    mylog = setup(log_filename)
    mylog.info('\n'
                'USER: ' + str(os.getlogin()) + '\n'
                'OPERATING SYSTEM: ' + str(platform.uname()) + '\n'
                'PYTHON VERSION:: ' + str(platform.python_version()) + '\n'
                'FILE: ' + filepathname + '\n'
                '========== STARTING =========='
                )

    # Return mylog instance.
    return mylog


def term_logfile(mylog: logging.Logger, filename: str) -> None:
    ''' Add log footer

    INPUT:
      - mylog (logger) = logger instance
      - modulefilepathname (str) = module file path and name (e.g. __file__)

    OUTPUT:
      - NONE (creates logging record message)
    '''
    mylog.info('\n'
                '========== ENDING ==========\n'
                'FILE: ' + filename
                )


# Usage example
if __name__ == '__main__':
    # Configure command line interface arguments plus help and usage messages
    args = get_cli_help()

    try: # Code to execute, at least until an exception occurs
        # Configure logging per command line options
        if args.logtype[0] == '1':
            mylog = setup()
        elif args.logtype[0] == '2':
            mylog = init_logfile(args.logpath, __file__)
        else:
            mylog = setup(args.logpathfilename)

        # Process module's Python code.
        print('⬛ User Console Message: Trying actions.')
        mylog.info('Trying actions.')

        if args.is_test_exception_specified:
            # test specified ZeroDivisionError exception handling
            some_variable = 1 / 0
        
        if args.is_test_exception_unspecified:
            # Test unspecified exception handling
            raise Exception('🟥 Oh, golly. Something really bad unexpectedly happened.')
    
        mylog.debug(
            'TEST: Message with critical details to help identify'
            ' and resolve problems. Generally, displayed only in'
            ' DEVELOPMENT environment; typically, suppressed in TEST and'
            ' PRODUCTION environments.'
        )
        mylog.info(
            'TEST: Message to confirm execution is working as'
            ' expected. Generally, displayed only in DEVELOPMENT'
            ' environment; typically, suppressed in TEST and PRODUCTION'
            ' environments.'
        )
        mylog.warning(
            'TEST: Message indicating that an unexpected minor problem'
            ' happened, or will likely happen in the near future (e.g.'
            ' disk space low), even though execution is currently working'
            ' as expected.'
        )
        mylog.error(
            'TEST: Message indicating that an unexpected serious problem'
            ' has occurred, which prevented some code or function to finish'
            ' executing as expected. State that results are likely invalid'
            ' or unreliable. Suggest 2 or 3 of the most common causes and'
            ' related corrective actions. Refer to a specific, credible'
            ' help article title and URL. Recommend contacting the help'
            ' desk if errors continue. Offer several contact response'
            ' levels depending on the user\'s urgency. Provide help desk'
            ' contact information; e.g. online form, email address, chat'
            ' URL, phone number.'
        )
        mylog.critical(
            'TEST: Message indicating that an unexpected near-fatal'
            ' or fatal problem has occurred, which will very likely'
            ' prevent any further execution to occur. State that results'
            ' are very likely invalid or unreliable. Suggest 2 or 3 of the'
            ' most common causes and related corrective actions. Refer to'
            ' a specific, credible help article title and URL. Recommend'
            ' contacting the help desk if errors continue. Offer several'
            ' contact response levels depending on the user\'s urgency.'
            ' Provide help desk contact information; e.g. online form,'
            ' email address, chat URL, phone number.'
        )
        
        # Notify user that successful execution has completed.
        if args.logtype[0] == '1':
            mylog.info(' 🟩 SUCCESSFUL EXECUTION: See output displayed above.')
        elif args.logtype[0] == '2':
            mylog.info(' 🟩 SUCCESSFUL EXECUTION: See output in most recent log file in ' + args.logpath)
        else:
            mylog.info(' 🟩 SUCCESSFUL EXECUTION: See output in ' + args.logpathfilename)

        mylog.info('🟩 Completed actions successfully.')
    except ZeroDivisionError: # Code to handle specific exception
        mylog.exception(
            'Oops! Something went wrong. The application tried to do a'
            ' math problem where it tried to divide a number by zero,'
            ' but that is impossible to do. So the program stopped to'
            ' make sure it doesn\'t give you any wrong or unreliable'
            ' information.\n'
            '\n'
            'But, don\'t worry! Let\'s figure out what went wrong and'
            ' get you back on track. First, please double-check the'
            ' information you entered. Make sure everything is correct'
            ' and matches what you intended. If there\'s anything that'
            ' needs to be changed, go ahead and fix it.\n'
            '\n'
            'If you\'re still having trouble, we\'re here to help! You'
            ' can reach out to our support team in a way that\'s most'
            ' convenient for you.\n'
            '\n'
            'If you like chatting online, you can connect with a'
            ' support team member on our website at'
            ' support-chat.domain.tld. They\'re available all the time'
            ' to assist you.\n'
            '\n'
            'If you prefer talking on the phone, you can call us at'
            ' 800-555-1234 on weekdays between 9 AM and 5 PM Central'
            ' Time.\n'
            '\n'
            'If you want to send us a message and get a response by'
            ' email, you can use our online support request form at'
            ' support-form.domain.tld. We\'ll make sure to get back'
            ' to you within 1 to 2 business days.\n'
            '\n'
            'We\'re here to make sure everything runs smoothly for'
            ' you, so don\'t hesitate to get in touch.\n'
            '\n'
            'Technical Error Details to Share with Our Help Desk Team:'
        )
    except Exception as e: # Code to handle unspecified exception
        mylog.exception(
            '🟥 Oops! Something went wrong. The application stopped to'
            ' make sure it doesn\'t give you any wrong or unreliable'
            ' information.\n'
            '\n'
            'But, don\'t worry! Let\'s figure out what went wrong and'
            ' get you back on track. First, please double-check the'
            ' information you entered. Make sure everything is correct'
            ' and matches what you intended. If there\'s anything that'
            ' needs to be changed, go ahead and fix it.\n'
            '\n'
            'If you\'re still having trouble, we\'re here to help! You'
            ' can reach out to our support team in a way that\'s most'
            ' convenient for you.\n'
            '\n'
            'If you like chatting online, you can connect with a'
            ' support team member on our website at'
            ' support-chat.domain.tld. They\'re available all the time'
            ' to assist you.\n'
            '\n'
            'If you prefer talking on the phone, you can call us at'
            ' 800-555-1234 on weekdays between 9 AM and 5 PM Central'
            ' Time.\n'
            '\n'
            'If you want to send us a message and get a response by'
            ' email, you can use our online support request form at'
            ' support-form.domain.tld. We\'ll make sure to get back'
            ' to you within 1 to 2 business days.\n'
            '\n'
            'We\'re here to make sure everything runs smoothly for'
            ' you, so don\'t hesitate to get in touch.\n'
            '\n'
            'Technical Error Details to Share with Our Help Desk Team:'
        )


    finally: # Code to always execute, even if an exception occurs
        if args.logtype[0] == '2':
            term_logfile(mylog, __file__)