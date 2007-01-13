#!/usr/bin/env python
"""
Get version of Hachoir and display it on stdout with end of line.
Eg. "0.4.1"
"""
if __name__ == "__main__":
    import os
    import sys
    root_dir = os.path.dirname(__file__)
    sys.path.append(root_dir)
    import hachoir_core
    print hachoir_core.__version__

