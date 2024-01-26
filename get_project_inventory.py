import lib.utils.logz
mylog = lib.utils.logz.init_logfile('logs\\', __file__).getChild('get_project_inventory')

from lib.classes.dev_proj_dir import DevelopmentProjectDirectory


if __name__ == '__main__':
    try: # Code to execute, at least until an exception occurs.
        mylog.info('Trying Actions…')
        
        # module code to execute.
        project_inventory = DevelopmentProjectDirectory()
        project_inventory.dirpathname = input(r'Enter project directory pathname (e.g. D:\path\to\proj\dir): ')
        project_inventory.directories_excluded = ['.git', '__pycache__', 'docs', 'logs', 'ztrash']
        project_inventory.module_extensions_included = ['.py']
        project_inventory.save_development_inventory_report()

        mylog.info('🟩 …Completed Actions.')
    # … optional code to handle specified exceptions …
    except Exception: # Code to handle unspecified exceptions
        mylog.exception('🟥🟥 FATAL ERROR: UNEXPECTED EXCEPTION OCCURRED!',
                        exc_info = True
        )
    finally: # Code to always execute, even if an exception occurs
        lib.utils.logz.term_logfile(mylog, __file__)

        
'''
Roadmap:

    for each object type:
        min
        median
        max

        95% confidence interval 
            lower
            mean
            upper 

        guidelines 
            lower
            mean
            upper

            examples
                package  ~54 modules

                module ~300 - 400 lines

                classes < 20 functions 
                function ~5 - 20 lines 
'''