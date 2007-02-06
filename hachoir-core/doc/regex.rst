Create regular expressions
==========================

There is two ways to create regular expressions: use string or directly
use the API.

Create regex with string
------------------------

>>> from hachoir_core.regex import parse
>>> parse('')
<RegexEmpty ''>
>>> parse('abc')
<RegexString 'abc'>
>>> parse('[bc]d')
<RegexAnd '[bc]d'>
>>> parse('a(b|[cd]|(e|f))g')
<RegexAnd 'a[b-f]g'>
>>> parse('([a-z]|[b-])')
<RegexRange '[a-z-]'>
>>> parse('^^..$$')
<RegexAnd '^..$'>
>>> parse('chats?')
<RegexRepeat 'chats?'>
>>> parse(' +abc')
<RegexAnd ' +abc'>

Create regex with the API
-------------------------

>>> from hachoir_core.regex import createString, createRange
>>> createString('')
<RegexEmpty ''>
>>> createString('abc')
<RegexString 'abc'>
>>> createRange('a', 'b', 'c')
<RegexRange '[a-c]'>
>>> createRange('a', 'b', 'c', exclude=True)
<RegexRange '[^a-c]'>


Manipulate regular expressions
==============================

Convert to string:

>>> from hachoir_core.regex import createRange, createString
>>> str(createString('abc'))
'abc'
>>> repr(createString('abc'))
"<RegexString 'abc'>"

Operatiors "and" and "or":

>>> createString("bike") & createString("motor")
<RegexString 'bikemotor'>
>>> createString("bike") | createString("motor")
<RegexOr '(bike|motor)'>

You can also use operator "+", it's just an alias to a & b:

>>> createString("big ") + createString("bike")
<RegexString 'big bike'>

Compute minimum/maximum matched pattern:

>>> r=parse('(cat|horse)')
>>> r.minLength(), r.maxLength()
(3, 5)


Optimizations
=============

The library includes many optimization to keep small and fast expressions.

Group prefix/suffix:

>>> createString("blue") | createString("brown")
<RegexAnd 'b(lue|rown)'>
>>> createString("mot") | createString("pot")
<RegexAnd '[mp]ot'>
>>> createString("moto") | parse("mot.")
<RegexAnd 'mot(.|o)'>

Merge ranges:

>>> from hachoir_core.regex import createRange
>>> regex = createString("1") | createString("3"); regex
<RegexRange '[13]'>
>>> regex = regex | createRange("2"); regex
<RegexRange '[1-3]'>
>>> regex = regex | createString("0"); regex
<RegexRange '[0-3]'>
>>> regex = regex | createRange("5", "6"); regex
<RegexRange '[0-356]'>
>>> regex = regex | createRange("4"); regex
<RegexRange '[0-6]'>

