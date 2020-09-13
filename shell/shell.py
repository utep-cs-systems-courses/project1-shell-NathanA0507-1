import os, sys, re, time


while True:
    # \033[1;34;40m changes the color to blue and \x1b[0m changes it back to normal
    # This was done in an attempt to make the shell more readable
    args = input("\033[1;34;40m %s\x1b[0m$ " % os.getcwd())

    args = args.split(' ')

    # print(args)

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

    else:
        rc = os.fork()

        if rc < 0:
            os.write(2, ("fork failed, returning %d\n" % rc).encode())
            sys.exit(1)
        elif rc == 0:                   # child
            try:
                if '>' in args:
                    os.close(1)  # redirect child's stdout
                    os.open(args[args.index('>')+1], os.O_CREAT | os.O_WRONLY)
                    os.set_inheritable(1, True)
                    args.remove(args[args.index('>')+1])  # lol what does this even mean
                    args.remove('>')
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
        else:                           # parent (forked ok)
            val = os.wait()
            if val[1] != 0:
                os.write(2, ("Program terminated with exit code: %d\n" % val[1]).encode())