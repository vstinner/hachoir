Regex regression (repeat)
=========================

Factorisation of (a{n,p}){x,y}:
-------------------------------

>>> from hachoir.regex import parse
>>> parse(b"(a{2,3}){4,5}")
<RegexRepeat b'a{8,15}'>
>>> parse(b"(a{2,}){3,4}")
<RegexRepeat b'a{6,}'>
>>> parse(b"(a{2,3})+")
<RegexRepeat b'a{2,}'>
>>> parse(b"(a*){2,3}")
<RegexRepeat b'a*'>
>>> parse(b"(a+){2,3}")
<RegexRepeat b'a{2,}'>

Factorisation of (a|b)*:
------------------------

>>> parse(b"(a*|b)*")
<RegexRepeat b'[ab]*'>
>>> parse(b"(a+|b)*")
<RegexRepeat b'[ab]*'>
>>> parse(b"(a{2,}|b)*")
<RegexRepeat b'(a{2}|b)*'>

Factorisation of (a|b)+:
------------------------

>>> parse(b"(a*|b)+")
<RegexRepeat b'[ab]*'>
>>> parse(b"(a+|b|)+")
<RegexRepeat b'[ab]*'>
>>> parse(b"(a+|b)+")
<RegexRepeat b'[ab]+'>
>>> parse(b"(a{5,}|b)+")
<RegexRepeat b'(a{5}|b)+'>

Factorisation of (a|b){x,}:
---------------------------

>>> parse(b"(a+|b){3,}")
<RegexRepeat b'[ab]{3,}'>
>>> parse(b"(a{2,}|b){3,}")
<RegexRepeat b'(a{2}|b){3,}'>

Factorisation of (a|b){x,y}:
----------------------------

>>> parse(b"(a*|b|){4,5}")
<RegexRepeat b'(a+|b){0,5}'>
>>> parse(b"(a+|b|){4,5}")
<RegexRepeat b'(a+|b){0,5}'>
>>> parse(b"(a*|b){4,5}")
<RegexRepeat b'(a*|b){4,5}'>

Do not optimize:
----------------

>>> parse(b'(a*|b){3,}')
<RegexRepeat b'(a*|b){3,}'>
>>> parse(b"(a{2,3}|b){3,}")
<RegexRepeat b'(a{2,3}|b){3,}'>
>>> parse(b"(a{2,3}|b)*")
<RegexRepeat b'(a{2,3}|b)*'>
>>> parse(b"(a{2,3}|b)+")
<RegexRepeat b'(a{2,3}|b)+'>
>>> parse(b"(a+|b){4,5}")
<RegexRepeat b'(a+|b){4,5}'>
>>> parse(b"(a{2,}|b){4,5}")
<RegexRepeat b'(a{2,}|b){4,5}'>
>>> parse(b"(a{2,3}|b){4,5}")
<RegexRepeat b'(a{2,3}|b){4,5}'>


Regex regression (b)
====================

>>> from hachoir.regex import parse
>>> parse(b"(M(SCF|Thd)|B(MP4|Zh))")
<RegexOr b'(M(SCF|Thd)|B(MP4|Zh))'>
>>> parse(b"(FWS1|CWS1|FWS2|CWS2)")
<RegexOr b'(FWS[12]|CWS[12])'>
>>> parse(b"(abcdeZ|abZ)")
<RegexAnd b'ab(cdeZ|Z)'>
>>> parse(b"(00t003|10t003|00[12]0[1-9].abc\0|1CD001)")
<RegexOr b'(00(t003|[12]0[1-9].abc\0)|1(0t003|CD001))'>

