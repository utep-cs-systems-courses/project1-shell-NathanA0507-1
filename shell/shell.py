#! /usr/bin/env python3
import os, sys, re


def run_process(args):
    #  this try/except hands IO redirection
    try:
        if '>' in args:  # Output redirection
            os.close(1)  # redirect child's stdout
            os.open(args[args.index('>') + 1], os.O_CREAT | os.O_WRONLY)
            os.set_inheritable(1, True)
            args.remove(args[args.index('>') + 1])  # Remove the file name from the args list
            args.remove('>')  # Remove the '>' character from the arguments list

        if '<' in args:  # Input redirection
            os.close(0)  # redirect child's stdin
            os.open(args[args.index('<') + 1], os.O_RDONLY)  # Open the file in readonly
            os.set_inheritable(0, True)
            args.remove(args[args.index('<') + 1])  # Remove the file name from the args list
            args.remove('<')  # Remove the '<' character from the arguments list

    except IndexError:
        os.write(2, "Invalid input for redirection\n".encode())
    try:
        if args[0][0] == '/':
            os.execve(args[0], args, os.environ)  # try to exec program
    except FileNotFoundError:  # ...expected
        pass
    except IndexError:
        quit(1)
    except Exception: #  If the program doesn't work for some other reason just quit
        quit(1)

    for dir in re.split(":", os.environ['PATH']):  # try each directory in path
        program = "%s/%s" % (dir, args[0])
        try:
            os.execve(program, args, os.environ)  # try to exec program
        except FileNotFoundError:  # ...expected
            pass
        except Exception: #  If the program doesn't work for some other reason just quit
            quit(1)
    os.write(2, ("%s: Command not found\n" % args[0]).encode())
    quit(1)


def pipe(args):
    writeCommands = args[0:args.index("|")]
    readCommands = args[args.index("|") + 1:]
    pr, pw = os.pipe()
    rc = os.fork()
    if rc < 0:
        os.write(2, ("fork failed, returning %d\n" % rc).encode())
        sys.exit(1)
    elif rc == 0:
        os.close(1)  # close fd 1 (output)
        os.dup2(pw, 1)  # duplicate pw in fd1
        for fd in (pr, pw):
            os.close(fd)  # close pw & pr
        run_process(writeCommands)  # Run the process as normal
        os.write(2, ("Could not exec %s\n" % writeCommands[0]).encode())
        sys.exit(1)
    else:
        os.close(0)  # close fd 0 (input)
        os.dup2(pr, 0)  # dup pr in fd0
        for fd in (pw, pr):
            os.close(fd)
        if "|" in readCommands:
            pipe(readCommands)
        run_process(readCommands)  # Run the process as normal
        os.write(2, ("Could not exec %s\n" % writeCommands[0]).encode())
        sys.exit(1)


def command_handler(args):
    if len(args) == 0:
        return

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
        # fork1 ensures that the shell keeps running after the pipe occurs
        fork1 = os.fork()
        if fork1 < 0:
            os.write(2, ("fork failed, returning %d\n" % fork1).encode())
            sys.exit(1)
        elif fork1 == 0:
            pipe(args)


        else:  # parent (forked ok)
            if args[-1] != "&":  # If the command is to be run in the background don't wait, otherwise wait
                val = os.wait()
                if val[1] != 0 and val[1] != 256:
                    os.write(2, ("Program terminated with exit code: %d\n" % val[1]).encode())

    else:
        rc = os.fork()

        # By default, the shell will wait for a program to finish. If & is present, it will not
        wait = True

        if "&" in args:
            wait = False
            args.remove("&")

        if rc < 0:  # check if fork was successful
            os.write(2, ("fork failed, returning %d\n" % rc).encode())
            sys.exit(1)
        elif rc == 0:  # child
            run_process(args)
        else:  # parent (forked ok)
            if wait:
                val = os.wait()
                if val[1] != 0 and val[1] != 256:
                    os.write(2, ("Program terminated with exit code: %d\n" % val[1]).encode())






while True:
    # \033[1;34;40m changes the color to blue and \x1b[0m changes it back to normal
    # This was done in an attempt to make the shell more readable

    prompt = "\033[1;34;40m %s\x1b[0m$ " % os.getcwd()
    if 'PS1' in os.environ:
        prompt = os.environ['PS1']

    try:
        os.write(1, prompt.encode())
        args = " "  # give the args some initial value so the loop starts (will be removed later with split())
        next_command = []
        while args != "":  # While there are still arguments
            args = args + os.read(0, 1024).decode()  # append new arguments to the previous command
            if "\n" in args:
                args = args.split("\n")  # split based on newline characters
                next_command = next_command + args[1:]  # args[1] is the next command, so we ignore it for now
                args = args[0].split()  # We know that args[0] is all our current command so we split and send
                command_handler(args)  # This method handles forking/exec/checking for IO redirect symbols, etc
                while len(next_command[0]) == 0 and len(next_command > 1):
                    next_command = next_command[1:]
                args = next_command  # we update args to now be the next command that we're working with
                print("help", next_command)
                next_command = next_command[1:]

    except EOFError:
        quit(1)
