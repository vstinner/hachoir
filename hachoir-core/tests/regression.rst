Regression tests
================

Regex
-----

>>> from hachoir_core.regex import parse
>>> parse("(M(SCF|Thd)|B(MP4|Zh))")
<RegexOr '(M(SCF|Thd)|B(MP4|Zh))'>

Old bug => '([BM](SCF|Thd|MP4|Zh))'

