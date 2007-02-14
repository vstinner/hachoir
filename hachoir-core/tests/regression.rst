Regression tests
================

Regex
-----

>>> from hachoir_core.regex import parse
>>> parse("(M(SCF|Thd)|B(MP4|Zh))")
<RegexOr '(M(SCF|Thd)|B(MP4|Zh))'>

Old bug => '([BM](SCF|Thd|MP4|Zh))'

>>> parse("(FWS1|CWS1|FWS2|CWS2)")
<RegexAnd '[CF]WS[12]'>

It wasn't optimized: <RegexOr '([CF]WS1|[CF]WS2)'>

>>> parse("(abcdeZ|abZ)")
<RegexAnd 'ab(cdeZ|Z)'>

Don't optimize to: <RegexAnd 'ab(cde|)Z'>

