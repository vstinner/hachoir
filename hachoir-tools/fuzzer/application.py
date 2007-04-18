from sys import platform

if platform == 'win32':
    from app_win32 import Application
else:
    from app_unix import Application

