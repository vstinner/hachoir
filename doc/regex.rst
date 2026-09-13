++++++++++++++++++++
hachoir.regex module
++++++++++++++++++++

``hachoir.regex`` is a Python library for regular expression (regex or regexp)
manupulation. You can use a|b (or) and a+b (and) operators. Expressions are
optimized during the construction: merge ranges, simplify repetitions, etc.  It
also contains a class for pattern matching allowing to search multiple strings
and regex at the same time.

Regex examples
==============

Regex are optimized during their creation::

   >>> from hachoir.regex import parse, createRange, createString
   >>> createString(b"bike") + createString(b"motor")
   <RegexString b'bikemotor'>
   >>> parse(b'(foo|fooo|foot|football)')
   <RegexAnd b'foo(|[ot]|tball)'>

Create character range::

   >>> regex = createString(b"1") | createString(b"3")
   >>> regex
   <RegexRange b'[13]'>
   >>> regex |= createRange(b"2", b"4")
   >>> regex
   <RegexRange b'[1-4]'>

As you can see, you can use classic "a|b" (or) and "a+b" (and)
Python operators. Example of regular expressions using repetition::

   >>> parse(b"(a{2,}){3,4}")
   <RegexRepeat b'a{6,}'>
   >>> parse(b"(a*|b)*")
   <RegexRepeat b'[ab]*'>
   >>> parse(b"(a*|b|){4,5}")
   <RegexRepeat b'(a+|b){0,5}'>

Compute minimum/maximum matched pattern::

   >>> r=parse(b'(cat|horse)')
   >>> r.minLength(), r.maxLength()
   (3, 5)
   >>> r=parse(b'(a{2,}|b+)')
   >>> r.minLength(), r.maxLength()
   (1, None)

Pattern maching
===============

Use PatternMaching if you would like to find many strings or regex in a string.
Use addString() and addRegex() to add your patterns::

    >>> from hachoir.regex import PatternMatching
    >>> p = PatternMatching()
    >>> p.addString(b"a")
    >>> p.addString(b"b")
    >>> p.addRegex(b"[cd]")

And then use search() to find all patterns::

    >>> for start, end, item in p.search(b"a b c d"):
    ...    print("%s..%s: %s" % (start, end, item))
    ...
    0..1: b'a'
    2..3: b'b'
    4..5: b'[cd]'
    6..7: b'[cd]'

You can also attach an object to a pattern with 'user' (user data) argument::

    >>> p = PatternMatching()
    >>> p.addString(b"un", 1)
    >>> p.addString(b"deux", 2)
    >>> for start, end, item in p.search(b"un deux"):
    ...    print("%r at %s: user=%r" % (item, start, item.user))
    ...
    <StringPattern b'un'> at 0: user=1
    <StringPattern b'deux'> at 3: user=2

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

::

    >>> from hachoir.regex import parse
    >>> parse(b'')
    <RegexEmpty b''>
    >>> parse(b'abc')
    <RegexString b'abc'>
    >>> parse(b'[bc]d')
    <RegexAnd b'[bc]d'>
    >>> parse(b'a(b|[cd]|(e|f))g')
    <RegexAnd b'a[b-f]g'>
    >>> parse(b'([a-z]|[b-])')
    <RegexRange b'[a-z-]'>
    >>> parse(b'^^..$$')
    <RegexAnd b'^..$'>
    >>> parse(b'chats?')
    <RegexAnd b'chats?'>
    >>> parse(b' +abc')
    <RegexAnd b' +abc'>

Create regex with the API
-------------------------

::

    >>> from hachoir.regex import createString, createRange
    >>> createString(b'')
    <RegexEmpty b''>
    >>> createString(b'abc')
    <RegexString b'abc'>
    >>> createRange(b'a', b'b', b'c')
    <RegexRange b'[a-c]'>
    >>> createRange(b'a', b'b', b'c', exclude=True)
    <RegexRange b'[^a-c]'>


Manipulate regular expressions
==============================

Convert to string::

    >>> from hachoir.regex import createRange, createString
    >>> bytes(createString(b'abc'))
    b'abc'
    >>> str(createString(b'abc'))
    "b'abc'"
    >>> repr(createString(b'abc'))
    "<RegexString b'abc'>"

Operatiors "and" and "or"::

    >>> createString(b"bike") & createString(b"motor")
    <RegexString b'bikemotor'>
    >>> createString(b"bike") | createString(b"motor")
    <RegexOr b'(bike|motor)'>

You can also use operator "+", it's just an alias to a & b::

    >>> createString(b"big ") + createString(b"bike")
    <RegexString b'big bike'>

Compute minimum/maximum matched pattern::

    >>> r=parse(b'(cat|horse)')
    >>> r.minLength(), r.maxLength()
    (3, 5)


Optimizations
=============

The library includes many optimization to keep small and fast expressions.

Group prefix::

    >>> createString(b"blue") | createString(b"brown")
    <RegexAnd b'b(lue|rown)'>
    >>> createString(b"moto") | parse(b"mot.")
    <RegexAnd b'mot.'>
    >>> parse(b"(ma|mb|mc)")
    <RegexAnd b'm[a-c]'>
    >>> parse(b"(maa|mbb|mcc)")
    <RegexAnd b'm(aa|bb|cc)'>

Merge ranges::

    >>> from hachoir.regex import createRange
    >>> regex = createString(b"1") | createString(b"3"); regex
    <RegexRange b'[13]'>
    >>> regex = regex | createRange(b"2"); regex
    <RegexRange b'[1-3]'>
    >>> regex = regex | createString(b"0"); regex
    <RegexRange b'[0-3]'>
    >>> regex = regex | createRange(b"5", b"6"); regex
    <RegexRange b'[0-356]'>
    >>> regex = regex | createRange(b"4"); regex
    <RegexRange b'[0-6]'>


PatternMaching class
====================

Use PatternMaching if you would like to find many strings or regex in a string.
Use addString() and addRegex() to add your patterns::

    >>> from hachoir.regex import PatternMatching
    >>> p = PatternMatching()
    >>> p.addString(b"a")
    >>> p.addString(b"b")
    >>> p.addRegex(b"[cd]")

And then use search() to find all patterns::

    >>> for start, end, item in p.search(b"a b c d"):
    ...    print("%s..%s: %s" % (start, end, item))
    ...
    0..1: b'a'
    2..3: b'b'
    4..5: b'[cd]'
    6..7: b'[cd]'

Item is a Pattern object, not the matched string. To be exact, it's a
StringPattern for string and a RegexPattern for regex. You can associate an
"user" value to each Pattern object::

    >>> p2 = PatternMatching()
    >>> p2.addString(b"un", 1)
    >>> p2.addString(b"deux", 2)
    >>> p2.addRegex(b"(trois|three)", 3)
    >>> for start, end, item in p2.search(b"un deux trois"):
    ...    print("%r at %s: user=%r" % (item, start, item.user))
    ...
    <StringPattern b'un'> at 0: user=1
    <StringPattern b'deux'> at 3: user=2
    <RegexPattern b't(rois|hree)'> at 8: user=3

You can associate any Python object to an item, not only an integer!

