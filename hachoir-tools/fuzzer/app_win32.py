from base_app import BaseApplication
from win32api import TerminateProcess

class Application(BaseApplication):
    def interrupt(self):
        self.kill()

    def kill(self):
        hdl = int(self._process._handle)
        TerminateProcess(handle, -1)

