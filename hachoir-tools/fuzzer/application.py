from os import waitpid, P_NOWAIT, kill, \
    WCOREDUMP, WIFSIGNALED, WSTOPSIG, WIFEXITED, WEXITSTATUS
from subprocess import Popen, PIPE, STDOUT
from errno import ENOENT, ECHILD, ESRCH
from select import select
from time import time, sleep
from signal import SIGABRT, SIGFPE, SIGHUP, SIGINT, SIGSEGV, SIGKILL

SIGNAME = {
    SIGABRT: "SIGABRT",
    SIGINT: "SIGINT",
    SIGHUP: "SIGHUP",
    SIGFPE: "SIGFPE",
    SIGKILL: "SIGKILL",
    SIGSEGV: "SIGSEGV",
}

class Application:
    def __init__(self, program, args=None):
        self.program = program
        if args:
            self.args = list(args)
        else:
            self.args = []
        self.process = None
        self.exit_failure = None

    def start(self):
        try:
            args = [self.program] + self.args
            self.process = Popen(args, stdout=PIPE, stderr=STDOUT)
        except OSError, err:
            if err[0] == ENOENT:
                raise RuntimeError("No such program: %s" % self.program)
            else:
                raise

    def info(self, message):
        print "INFO: %s" % message

    def warning(self, message):
        print "WARNING: %s" % message

    def error(self, message):
        print "ERROR: %s" % message

    def readline(self, timeout=0, stream="stdout"):
        """
        Read one line from specified stream ('stdout' by default).

        timeout argument:
        - 0 (default): non-blocking read
        - None: blocking read
        - (float value): read with specified timeout in second

        Return a string with new line or None if their is no data.

        Code based on this code:
           http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/440554
        """
        if not self.process:
            return None

        out = getattr(self.process, stream)
        if not out:
            raise RuntimeError("Stream %s of process %s is not a pipe" % (stream, self))
        if timeout is not None:
            ready = select([out.fileno()], [], [], timeout)[0]
            if not ready:
                return None
        line = out.readline()
        if not line:
            return None
        line = line.rstrip()
        return line

    def readlines(self, timeout=0, total_timeout=None, stream="stdout"):
        if total_timeout:
            stop = time() + total_timeout
        else:
            stop = None
        while True:
            if stop:
                timeout = stop - time()
            line = self.readline(timeout, stream)
            if stop:
                if line is not None:
                    yield line
                if stop < time():
                    break
            else:
                if line is None:
                    break
                yield line


    def processOutput(self):
        line = None
        for line in self.readlines():
            if "Corrupt image" in line:
                print "ERR: Corrupt"
                return False
            if "Improper image header" in line:
                print "ERR: Image header"
                return False
            if "Unexpected end-of-file" in line:
                print "ERR: EOF"
                return False
            if "Insufficient image data in file" in line:
                print "Data underflow"
                return False
#        if line:
            print "last output line> %r" % line
        return None

    def exited(self, status):
        code = self.processOutput()
        if code is not None:
            self.exit_failure = code
            return

        # Display exit code
        if status is not None:
            log_func = self.warning
            info = []
            if WCOREDUMP(status):
                info.append("core.%s dumped!" % self.process.pid)
                self.exit_failure = True
                log_func = self.error
            if WIFSIGNALED(status):
                signal = WSTOPSIG(status)
#                signal = SIGNAME.get(signal, signal)
                self.exit_failure = True
                info.append("signal %s" % signal)
            if WIFEXITED(status):
                code = WEXITSTATUS(status)
                info.append("exitcode=%s" % code)
                self.exit_failure = 0
                # FIXME: identify returns 1 on mangled TTF font
#                self.exit_failure = (code != 0)
            if self.exit_failure:
                if info:
                    log_func("Exit (%s)" % ", ".join(info))
                else:
                    log_func("Exit")
        else:
            self.exit_failure = True
            self.error("Process exited (ECHILD error)")

        # Delete process
        self.process = None


    def wait(self, blocking=True):
        if not self.process:
            return False
        try:
            if blocking:
                option = 0
            else:
                option = P_NOWAIT
            finished, status = waitpid(self.process.pid, option)
        except OSError, err:
            if err[0] == ECHILD:
                finished = True
                status = None
            else:
                raise
        if finished == 0:
            return True

        # Log exit code
        self.exited(status)
        return False

    def isRunning(self):
        return self.wait(False)

    def stop(self):
        """
        Send SIGINT signal and waiting until nuauth is stopped.
        """
        if not self.isRunning():
            return
        self.warning("stop()")

        # Log output
        for line in self.readlines():
            pass

        # Send first SIGINT
        self.kill(SIGINT)

        # Wait until process ends
        step = 1
        signal = False
        start_time = time()
        while self.isRunning():
            if 2.0 < (time() - start_time):
                signal = True
                start_time = time()
            if signal:
                signal = False
                step += 1
                if step <= 2:
                    self.kill(SIGINT)
                else:
                    self.kill(SIGKILL)
            try:
                sleep(0.250)
            except KeyboardInterrupt:
                self.info("Interrupted (CTRL+C)")
                signal = True

    def kill(self, signum, raise_error=True):
        if not self.process:
            if raise_error:
                raise RuntimeError("Unable to kill %s: it's not running" % self)

        # Log action
        name = SIGNAME.get(signum, signum)
        if signum in (SIGINT, SIGHUP):
            log_func = self.warning
        else:
            log_func = self.error
        log_func("kill(%s)" % name)

        # Send signal
        try:
            kill(self.process.pid, signum)
        except OSError, err:
            if err[0] == ESRCH:
                self.exited(None)
                raise RuntimeError(
                    "Unable to send signal %s to %s: process is dead"
                    % (name, self))
            else:
                raise

