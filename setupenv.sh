#Source this file to use hachoir unpacked right from svn.

#This is an sh script because only sh scripts can be sourced from sh.

#Why not erase PYTHONPATH ? Conservative option chosen.
#PYTHONPATH=""

export PYTHONPATH=`cat << EOF | /usr/bin/env python -
from os import environ, getcwd

subprojects=[ 
"hachoir-core",
"hachoir-parser",
"hachoir-editor",
"hachoir-metadata",
"hachoir-regex",
"hachoir-subfile"
]

cur_dir = getcwd()
path_list = environ["PYTHONPATH"].split(':')
try:
  #occurs when the path is set but empty
  path_list.remove('')
except ValueError:
  pass

for project in subprojects:
  path_item = "%s/%s" % (cur_dir, project)
  if path_item not in path_list:
    path_list.append(path_item)

#Here, the bash variable is set from Python s stdout
print ":".join(path_list)

EOF
`

