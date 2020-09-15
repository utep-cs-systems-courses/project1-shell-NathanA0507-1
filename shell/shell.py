#! /usr/bin/env python3
import os, sys, re, time


def run_process(args):
    #  this try/except hands IO redirection
    try:
        if '>' in args:
            os.close(1)  # redirect child's stdout
            os.open(args[args.index('>') + 1], os.O_CREAT | os.O_WRONLY)
            os.set_inheritable(1, True)
            args.remove(args[args.index('>') + 1])  # Remove the file name from the args list
            args.remove('>')  # Remove the '>' character from the arguments list

        if '<' in args:
            os.close(0)  # redirect child's stdout
            os.open(args[args.index('<') + 1], os.O_RDONLY)
            args.remove(args[args.index('<') + 1])
            os.set_inheritable(0, True)
            args.remove('<')  # Remove the '<' character from the arguments list

    except IndexError:
        os.write(2, "Invalid input for redirection\n".encode())

    for dir in re.split(":", os.environ['PATH']):  # try each directory in path
        program = "%s/%s" % (dir, args[0])
        try:
            os.execve(program, args, os.environ)  # try to exec program
        except FileNotFoundError:  # ...expected
            pass
        except Exception:
            quit(1)
    os.write(2, ("%s: Command not found\n" % args[0]).encode())
    quit(1)


while True:
    # \033[1;34;40m changes the color to blue and \x1b[0m changes it back to normal
    # This was done in an attempt to make the shell more readable

    prompt = "\033[1;34;40m %s\x1b[0m$ " % os.getcwd()
    if 'PS1' in os.environ:
        prompt = os.environ['PS1']

    args = input(prompt)

    args = args.split(' ')

    if args[0].lower() == 'exit':
        os.write(2, "Goodbye!\n".encode())
        quit(0)
    if args[0] == 'cd':
        try:
            os.chdir(args[1])
        except FileNotFoundError:
            os.write(2, ("Directory %s not found\n" % args[1]).encode())
        except IndexError:
            os.write(2, "Must write a directory to swap to\n".encode())

    elif "|" in args:
        # Needs to split args list real quick
        writeCommands = args[0:args.index("|")]
        readCommands = args[args.index("|") + 1:]

        pr, pw = os.pipe()

        rc = os.fork()

        if rc < 0:
            os.write(2, ("fork failed, returing %d\n" % rc).encode())
            sys.exit(1)
        elif rc == 0:

            os.close(1)
            os.dup2(pw, 1)

            for fd in (pr, pw):
                os.close(fd)

            run_process(writeCommands)

            os.write(2, ("Could not exec %s\n" % writeCommands[0]).encode())
            sys.exit(1)
        else:
            os.close(0)
            os.dup2(pr, 0)

            for fd in (pw, pr):
                os.close(fd)

            run_process(readCommands)
    else:
        rc = os.fork()

        if rc < 0:
            os.write(2, ("fork failed, returning %d\n" % rc).encode())
            sys.exit(1)
        elif rc == 0:  # child
            run_process(args)
        else:  # parent (forked ok)
            if args[-1] != "&":
                val = os.wait()
                if val[1] != 0 and val[1] != 256:
                    os.write(2, ("Program terminated with exit code: %d\n" % val[1]).encode())
