Create regular expressions
==========================

There is two ways to create regular expressions: use string or directly
use the API.

Atom classes:

 * RegexEmpty: empty regex (match nothing)
 * RegexStart, RegexEnd, RegexDot: symbols ^, $ and .
 * RegexString
 * RegexRange: character range like [a-z] or [^0-9]
 * RegexAnd
 * RegexOr
 * RegexRepeat

All classes are based on Regex class.

Create regex with string
------------------------

>>> from hachoir_regex import parse
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
<RegexAnd 'chats?'>
>>> parse(' +abc')
<RegexAnd ' +abc'>

Create regex with the API
-------------------------

>>> from hachoir_regex import createString, createRange
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

>>> from hachoir_regex import createRange, createString
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

Group prefix:

>>> createString("blue") | createString("brown")
<RegexAnd 'b(lue|rown)'>
>>> createString("moto") | parse("mot.")
<RegexAnd 'mot.'>
>>> parse("(ma|mb|mc)")
<RegexAnd 'm[a-c]'>
>>> parse("(maa|mbb|mcc)")
<RegexAnd 'm(aa|bb|cc)'>

Merge ranges:

>>> from hachoir_regex import createRange
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


PatternMaching class
====================

Use PatternMaching if you would like to find many strings or regex in a string.
Use addString() and addRegex() to add your patterns.

    >>> from hachoir_regex import PatternMatching
    >>> p = PatternMatching()
    >>> p.addString("a")
    >>> p.addString("b")
    >>> p.addRegex("[cd]")

And then use search() to find all patterns:

    >>> for start, end, item in p.search("a b c d"):
    ...    print "%s..%s: %s" % (start, end, item)
    ...
    0..1: a
    2..3: b
    4..5: [cd]
    6..7: [cd]

Item is a Pattern object, not the matched string. To be exact, it's a
StringPattern for string and a RegexPattern for regex. You can associate an
"user" value to each Pattern object.

    >>> p2 = PatternMatching()
    >>> p2.addString("un", 1)
    >>> p2.addString("deux", 2)
    >>> p2.addRegex("(trois|three)", 3)
    >>> for start, end, item in p2.search("un deux trois"):
    ...    print "%r at %s: user=%r" % (item, start, item.user)
    ...
    <StringPattern 'un'> at 0: user=1
    <StringPattern 'deux'> at 3: user=2
    <RegexPattern 't(rois|hree)'> at 8: user=3

You can associate any Python object to an item, not only an integer!

