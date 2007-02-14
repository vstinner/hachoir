Regression tests
================

Regex
-----

>>> from hachoir_core.regex import parse
>>> parse("(M(SCF|Thd)|B(MP4|Zh))")
<RegexOr '(M(SCF|Thd)|B(MP4|Zh))'>
>>> parse("(FWS1|CWS1|FWS2|CWS2)")
<RegexOr '(FWS[12]|CWS[12])'>
>>> parse("(abcdeZ|abZ)")
<RegexAnd 'ab(cdeZ|Z)'>
>>> parse("(00t003|10t003|00[12]0[1-9].abc\0|1CD001)")
<RegexOr '(00(t003|[12]0[1-9].abc\0)|1(0t003|CD001))'>

