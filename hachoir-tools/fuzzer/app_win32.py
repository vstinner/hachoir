from base_app import BaseApplication
from win32api import TerminateProcess
from win32process import GetExitCodeProcess
from win32event import WaitForSingleObject, INFINITE

class Application(BaseApplication):
    def _getHandle(self):
        assert self.process
        return int(self.process._handle)

    def interrupt(self):
        self.kill()

    def kill(self):
        TerminateProcess(self._getHandle(), -1)

    def _wait(self, blocking=True):
        self.exit_code = None
        self.exit_failure = False
        if blocking:
            timeout = INFINITE
        else:
            timeout = 0
        handle = self._getHandle()
        is_running = (WaitForSingleObject(handle, timeout) != 0)
        if not is_running:
            status = GetExitCodeProcess(handle)
            self.exit_failure = (status != 0)
            self.exit_code = status
        else:
            status = None
        return (is_running, status)

