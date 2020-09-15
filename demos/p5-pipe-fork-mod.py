#! /usr/bin/env python3

import os, sys, time, re

pid = os.getpid()               # get and remember pid

pr,pw = os.pipe()
for f in (pr, pw):
    os.set_inheritable(f, True)
#print("pipe fds: pr=%d, pw=%d" % (pr, pw))

import fileinput

#print("About to fork (pid=%d)" % pid)

rc = os.fork()

if rc < 0:
    #print("fork failed, returning %d\n" % rc, file=sys.stderr)
    sys.exit(1)

elif rc == 0:                   #  child - will write to pipe
    #print("Child: My pid==%d.  Parent's pid=%d" % (os.getpid(), pid), file=sys.stderr)
    args = ["ls"]

    os.close(1)                 # redirect child's stdout
    os.dup2(pw, 1)

    for fd in (pr, pw):
        os.close(fd)

    for dir in re.split(":", os.environ['PATH']): # try each directory in path
        program = "%s/%s" % (dir, args[0])
        try:
            os.execve(program, args, os.environ) # try to exec program
        except FileNotFoundError:             # ...expected
            pass




    os.write(2, ("Child:    Error: Could not exec %s\n" % args[0]).encode())
    sys.exit(1)

else:                           # parent (forked ok)
    args = ["grep", "txt"]

    #print("Parent: My pid==%d.  Child's pid=%d" % (os.getpid(), rc), file=sys.stderr)
    os.close(0)
    os.dup2(pr, 0)
    for fd in (pw, pr):
        os.close(fd)

    for dir in re.split(":", os.environ['PATH']): # try each directory in path
        program = "%s/%s" % (dir, args[0])
        try:
            os.execve(program, args, os.environ) # try to exec program
        except FileNotFoundError:             # ...expected
            pass

    #for line in fileinput.input():
        #print("From child: <%s>" % line)
