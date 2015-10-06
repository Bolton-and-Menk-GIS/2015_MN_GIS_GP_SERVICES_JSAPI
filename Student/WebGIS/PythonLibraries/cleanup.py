import os
import time
import shutil
import fnmatch
import operator
from datetime import datetime
from dateutil.relativedelta import relativedelta

def remove_folders(path, days=7, exclude=[], older_than=True, test=False, subdirs=True, del_gdb=False):
    """removes old folders within a certain amount of days from today

    Required:
        path -- root directory to delete folders from
        days -- number of days back to delete from.  Anything older than
            this many days will be deleted. Default is 7 days.

    Optional:
        exclude -- list of folders to skip over (supports wildcards).
            These directories will not be removed.
        older_than -- option to remove all folders older than a certain
            amount of days. Default is True.  If False, will remove all
            folders within the last N days.
        test -- Default is False.  If True, performs a test folder iteration,
            to print out the mock results and does not actually delete folders.
        subdirs -- iterate through all sub-directories. Default is False.
        del_gdb -- delete file geodatabases. Default is False
    """

    # get removal date and operator
    remove_after = datetime.now() - relativedelta(days=days)
    op = operator.lt
    if not older_than:
        op = operator.gt

    # optional test
    if test:
        def remove(*args): pass
    else:
        def remove(*args):
            shutil.rmtree(args[0], ignore_errors=True)

    # walk thru directory
    for root, dirs, files in os.walk(path):
        for d in dirs:
            if not d.endswith('.gdb'):
                if not any(map(lambda ex: fnmatch.fnmatch(d, ex), exclude)):
                    last_mod = datetime.fromtimestamp(os.path.getmtime(os.path.join(root, d)))

                    # check date
                    if op(last_mod, remove_after):
                        try:
                            remove(os.path.join(root, d))
                            print 'deleted: "{0}"'.format(os.path.join(root, d))
                        except:
                            print '\nCould not delete: "{0}"!\n'.format(os.path.join(root, d))
                    else:
                        print 'skipped: "{0}"'.format(os.path.join(root, d))
                else:
                    print 'excluded: "{0}"'.format(os.path.join(root, d))
            else:
                if del_gdb:
                    remove(os.path.join(root, d))
                    print 'deleted geodatabase: "{0}"'.format(os.path.join(root, d))
                else:
                    print 'excluded geodatabase: "{0}"'.format(os.path.join(root, d))

        # break or continue if checking sub-directories
        if not subdirs:
            break

    return

def remove_files(path, days=7, exclude=[], older_than=True, test=False, subdirs=False):
    """removes old folders within a certain amount of days from today

    Required:
        path -- root directory to delete files from
        days -- number of days back to delete from.  Anything older than
            this many days will be deleted. Default is 7 days.

    Optional:
        exclude -- list of folders to skip over (supports wildcards).
            These directories will not be removed.
        older_than -- option to remove all folders older than a certain
            amount of days. Default is True.  If False, will remove all
            files within the last N days.
        test -- Default is False.  If True, performs a test folder iteration,
            to print out the mock results and does not actually delete files.
        subdirs -- iterate through all sub-directories. Default is False.
    """

    # get removal date and operator
    remove_after = datetime.now() - relativedelta(days=days)
    op = operator.lt
    if not older_than:
        op = operator.gt

    # optional test
    if test:
        'print testing....\n'
        def remove(*args): pass
    else:
        def remove(*args):
            os.remove(args[0])

    # walk thru directory
    for root, dirs, files in os.walk(path):
        if not root.endswith('.gdb'):
            for f in files:
                if not f.lower().endswith('.lock'):
                    if not any(map(lambda ex: fnmatch.fnmatch(f, ex), exclude)):
                        last_mod = datetime.fromtimestamp(os.path.getmtime(os.path.join(root, f)))

                        # check date
                        if op(last_mod, remove_after):
                            try:
                                remove(os.path.join(root, f))
                                print 'deleted: "{0}"'.format(os.path.join(root, f))
                            except:
                                print '\nCould not delete: "{0}"!\n'.format(os.path.join(root, f))
                        else:
                            print 'skipped: "{0}"'.format(os.path.join(root, f))
                    else:
                        print 'excluded: "{0}"'.format(os.path.join(root, f))
                else:
                    print 'file is locked: "{0}"'.format(os.path.join(root, f))
        else:
            print 'excluded files in: "{0}"'.format(root)

        # break or continue if checking sub-directories
        if not subdirs:
            break

    return


if __name__ == '__main__':

    path = r'C:\TEMP'
    path = r'\\arcserver3\wwwroot\TempFiles'
##    remove_folders(path, 7, test=True, subdirs=1, del_gdb=0)
    print '\n' * 3
    remove_files(path, 1/24.0, subdirs=0)


