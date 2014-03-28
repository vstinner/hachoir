+++++++++++++
Hachoir Urwid
+++++++++++++

**hachoir-urwid** is the most sexy user interface based on
[[hachoir-parser|hachoir-parser]] to explore a binary file.

Command line options
====================

* ``--preload=10``: Load 10 fields when loading a new field set
* ``--path="/header/bpp"``: Open the specified path and focus on the field
* ``--parser=PARSERID``: Force a parser (and skip parser validation)


Usefull keys
============

Move:

* up/down: move up/down
* home: go to parent
* end: go to the last field of a field set
* left/right: horizontal scrolling

Setup display:

* h: most important option :-) switch between human display (default) and raw value
* v / d / s: show or hide field value / description / size
* a: switch between relative (default) and absolute address
* b: switch between address in decimal (default) and hexadecimal

Interaction:

* enter: on a field set, expand/collaspe the children
* space: parse a file/stream contained in the current field

Application:

* q: quit
* < / >: previous / next tab
* + / -: move separator vertically
* esc or CTRL+W: close current tab
* F1: display help


Help
====

Command line options: use --help option.

In hachoir-use, use F1 key to get help (keyboard keys).


Other Hachoir user interfaces
=============================

* [[hachoir-gtk]]
* [[hachoir-http]]
* [[hachoir-wx]]

