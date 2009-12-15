# Source this file to use hachoir unpacked right from svn.
# Written by Feth Arezki and Olivier Serres

# This is an sh script because only sh scripts can be sourced from sh.

#Why not erase PYTHONPATH ? Conservative option chosen.
#PYTHONPATH=""

if [ $0 == $BASH_SOURCE ] ; then
	echo "Please source this file to set your shell variables, don't execute it"
        echo "source $0"
	exit 1
fi

MY_NAME="setupenv.sh"

SETUPENV_DIR=` \
	echo ${BASH_SOURCE} |\

	#sed expressions :
	# 0 Changes non-absolute paths to absolute paths
	# 1 Removes file part of the path to retrieve the directory

	sed  \
		-e "s,^\([^/].*\),${PWD}/${BASH_SOURCE},"  \
		-e "s,${MY_NAME}$,,"`

eval `cat << EOF | /usr/bin/env python - ${SETUPENV_DIR}
"""
This script fetches PATH and PYTHONPATH. It issues some echo commands to
tell what's happening, and if needed, extends PATH and PYTHONPATH (also with
"export PATH=..." statements)
"""
from os import environ
from os import getcwd
from os.path import join
from os.path import realpath
from sys import argv

#can't guess file, we are stdin
cur_dir = realpath(argv[1])

subprojects = """
hachoir-core
hachoir-editor
hachoir-metadata
hachoir-parser
hachoir-qt
hachoir-regex
hachoir-subfile
"""

exe_dirs = """
hachoir-urwid
hachoir-metadata
hachoir-qt
"""

def _realpaths(partials):
  for partial in partials.split():
    yield(join(cur_dir, partial))

def _get_pathlist(name):
  pathlist = environ.get(name, '').split(':')
  while '' in pathlist:
    #happens around solitary ':'
    pathlist.remove('')
  return [realpath(item) for item in pathlist]

def _issuecmd(cmd):
  print cmd, ';'

def echo(msg):
  _issuecmd('echo %s' % msg)

def setvariable(variable, value):
  _issuecmd('export %s=%s' % (variable, value))

def newpath(needed_dirs, varname):
  """
  main function
  """
  orig_path = _get_pathlist(varname)
  unchanged = True
  for needed_dir in _realpaths(needed_dirs):
    if needed_dir not in orig_path:
      echo("%s: adding %s" % (varname, needed_dir))
      unchanged = False
      orig_path.append(needed_dir)
  if unchanged:
    echo("%s unchanged" % varname)
  else:
    value = ":".join(orig_path)
    setvariable(varname, value)
    echo("Set %s to %s" % (varname, value))

echo("Setting up env around %s" % cur_dir)
newpath(exe_dirs, 'PATH')
newpath(subprojects, 'PYTHONPATH')

EOF
`

