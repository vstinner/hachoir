Regex regression (repeat)
=========================

Factorisation of (a{n,p}){x,y}:
-------------------------------

>>> from hachoir_regex import parse
>>> parse("(a{2,3}){4,5}")
<RegexRepeat 'a{8,15}'>
>>> parse("(a{2,}){3,4}")
<RegexRepeat 'a{6,}'>
>>> parse("(a{2,3})+")
<RegexRepeat 'a{2,}'>
>>> parse("(a*){2,3}")
<RegexRepeat 'a*'>
>>> parse("(a+){2,3}")
<RegexRepeat 'a{2,}'>

Factorisation of (a|b)*:
------------------------

>>> parse("(a*|b)*")
<RegexRepeat '[ab]*'>
>>> parse("(a+|b)*")
<RegexRepeat '[ab]*'>
>>> parse("(a{2,}|b)*")
<RegexRepeat '(a{2}|b)*'>

Factorisation of (a|b)+:
------------------------

>>> parse("(a*|b)+")
<RegexRepeat '[ab]*'>
>>> parse("(a+|b|)+")
<RegexRepeat '[ab]*'>
>>> parse("(a+|b)+")
<RegexRepeat '[ab]+'>
>>> parse("(a{5,}|b)+")
<RegexRepeat '(a{5}|b)+'>

Factorisation of (a|b){x,}:
---------------------------

>>> parse("(a+|b){3,}")
<RegexRepeat '[ab]{3,}'>
>>> parse("(a{2,}|b){3,}")
<RegexRepeat '(a{2}|b){3,}'>

Factorisation of (a|b){x,y}:
----------------------------

>>> parse("(a*|b|){4,5}")
<RegexRepeat '(a+|b){0,5}'>
>>> parse("(a+|b|){4,5}")
<RegexRepeat '(a+|b){0,5}'>
>>> parse("(a*|b){4,5}")
<RegexRepeat '(a*|b){4,5}'>

Do not optimize:
----------------

>>> parse('(a*|b){3,}')
<RegexRepeat '(a*|b){3,}'>
>>> parse("(a{2,3}|b){3,}")
<RegexRepeat '(a{2,3}|b){3,}'>
>>> parse("(a{2,3}|b)*")
<RegexRepeat '(a{2,3}|b)*'>
>>> parse("(a{2,3}|b)+")
<RegexRepeat '(a{2,3}|b)+'>
>>> parse("(a+|b){4,5}")
<RegexRepeat '(a+|b){4,5}'>
>>> parse("(a{2,}|b){4,5}")
<RegexRepeat '(a{2,}|b){4,5}'>
>>> parse("(a{2,3}|b){4,5}")
<RegexRepeat '(a{2,3}|b){4,5}'>


Regex regression (b)
====================

>>> from hachoir_regex import parse
>>> parse("(M(SCF|Thd)|B(MP4|Zh))")
<RegexOr '(M(SCF|Thd)|B(MP4|Zh))'>
>>> parse("(FWS1|CWS1|FWS2|CWS2)")
<RegexOr '(FWS[12]|CWS[12])'>
>>> parse("(abcdeZ|abZ)")
<RegexAnd 'ab(cdeZ|Z)'>
>>> parse("(00t003|10t003|00[12]0[1-9].abc\0|1CD001)")
<RegexOr '(00(t003|[12]0[1-9].abc\0)|1(0t003|CD001))'>

