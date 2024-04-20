import os
import sys
import time
import glob
import re
import subprocess


print ("Starting log monitor application")

log_dir = "/scratch/ankurraj/ranker/log/"
err_msg = re.compile(r"^\[ERROR\]*")


def get_log_files():
    """
    get log files in dir
    :return:
    """
    log_pat = log_dir+"/*.log"
    log_files = glob.glob(log_pat)
    print(log_files)

    return log_files


def check_log(log_file):

    with open(log_file) as lf:
        m = err_msg.search(lf.read(), re.MULTILINE)
        if m:
            err = "Error in "+log_file+"  "+m.group(0)
            cmd = "echo [%s] | mail -s 'Error in ranking' ankur.raj@oracle.com" % err
            subprocess.call(cmd)

'''
#   1) When the process that dies is the session leader of a session that
#      is attached to a terminal device, SIGHUP is sent to all processes
#      in the foreground process group of that terminal device.\n
#   2) When the death of a process causes a process group to become
#      orphaned, and one or more processes in the orphaned group are
#      stopped, then SIGHUP and SIGCONT are sent to all members of the
#      orphaned group." [2] \n
#
# The first case can be ignored since the child is guaranteed not to have
# a controlling terminal.  The second case isn't so easy to dismiss.
# The process group is orphaned when the first child terminates and
# POSIX.1 requires that every STOPPED process in an orphaned process
# group be sent a SIGHUP signal followed by a SIGCONT signal.  Since the
# second child is not STOPPED though, we can safely forego ignoring the
# SIGHUP signal.  In any case, there are no ill-effects if it is ignored.
#
# import signal           # Set handlers for asynchronous events. \n
# signal.signal(signal.SIGHUP, signal.SIG_IGN) \n
'''

def createDaemon(si, so, se):

    """
    This method will be used for creating a daemon process which sets the current
    process to run in backgroud NOTE : just doing process_name & does not detach the
    current process from terminal see the notes inside source code for more details.
    Is ignoring SIGHUP necessary ? It's often suggested that the SIGHUP signal should
    be ignored before the second fork to avoid premature termination of the process.
    The reason is that when the first child terminates, all processes, e.g.
    the second child, in the orphaned group will be sent a SIGHUP. However, as part of
    the session management system, there are exactly two cases where SIGHUP is sent on
    the death of a process:

    :param si: standard input
    :param so: standard output
    :param se: standard error
    :return:
    """


    try:
        pid = os.fork()
    except OSError as e:
        sys.exit(1)

    if pid == 0:  # The first child.

        #  To become the session leader of this new session and
        #  the process group leader of the new process group,
        #  we call os.setsid().  The process is
        #  also guaranteed not to have a controlling terminal.
        os.setsid()

        try:
            # Fork a second child and exit immediately to prevent zombies.
            # This causes the second child process to be orphaned,
            # making the init process responsible for its cleanup.
            # And, since the first child is a session leader without
            # a controlling terminal, it's possible for
            # it to acquire one by opening a terminal in the future (System V-
            # based systems).  This second fork guarantees that the child is no
            # longer a session leader, preventing the daemon from ever acquiring
            # a controlling terminal.
            pid = os.fork()  # Fork a second child.
        except OSError as  e:
            sys.exit(1)

        if pid == 0:  # The second child.
            # Since the current working directory may be a mounted filesystem, we
            # avoid the issue of not being able to unmount the filesystem at
            # shutdown time by changing it to the root directory.
            os.chdir('/')
            # We probably don't want the file mode creation mask inherited from
            # the parent, so we give the child complete control over permissions.

            os.umask(0)
            os.dup2(si.fileno(), sys.stdin.fileno())
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())

        else:
            # exit() or _exit()?  See below.
            os._exit(0)  # Exit parent (the first child) of the second child.
    else:
        # exit() or _exit()?
        # _exit is like exit(), but it doesn't call any functions registered
        # with atexit (and on_exit) or any registered signal handlers.  It also
        # closes any open file descriptors.  Using exit() may cause all stdio
        # streams to be flushed twice and any temporary files may be unexpectedly
        # removed.  It's therefore recommended that child branches of a fork()
        # and the parent branch(es) of a daemon use _exit().
        os._exit(0)  # Exit parent of the first child.


def start_monitor():
    """

    :return:
    """
    while True:
        for lf in get_log_files():
            lf = lf.stirp()
            check_log(lf)

        time.sleep(3600)


if __name__ == "__main__":
    start_monitor()
