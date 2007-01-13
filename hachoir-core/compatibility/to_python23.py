import re
import sys

def replaceImport(regs):
    sys.stderr.write("[+] Import: %s\n" % regs.group(0))
    text = regs.group(1).split("\n")
    text = " \\\n".join(text)
    return "import %s" % text

def replaceGen(regs):
    sys.stderr.write("[+] Generator: %s\n" % regs.group(0))
    return "[%s]" % regs.group(1)

def replaceCallGen(regs):
    sys.stderr.write("[+] Call with generator: %s\n" % regs.group(0))
    return "%s([%s])" % (regs.group(1), regs.group(2))

#def replaceReversed(regs):
#    return "list(%s)[::-1]" % regs.group(1)

default = "python23"
if 1 < len(sys.argv):
    convert_to = sys.argv[1]
    if convert_to not in ("python23", "nofuture"):
        convert_to = default
else:
    convert_to = default

error = False
orig_content = sys.stdin.read()
try:
    expr_exclude = "][()"
    expr_a = r"\([^%s]*\)" % expr_exclude
    expr_aa = r"\([^%s]*\([^%s]*\)[^%s]*\)" % (expr_exclude, expr_exclude, expr_exclude)
    expr_b = r"\[[^%s]*\]" % expr_exclude
    expr_c = r"[^%s]" % expr_exclude
    expr = r"(?:%s|%s|%s|%s)+" % (expr_a, expr_aa, expr_b, expr_c)
    regex_import = re.compile(r"import \(([a-zA-Z0-9_,%s ]+)\)" % "\n")
    regex_gen = re.compile("\((%s for %s in %s)\)" % (expr, expr, expr))
#    regex_reversed = re.compile("reversed\((%s)\)" % expr)
    regex_call_gen = re.compile(
        "([a-zA-Z][a-zA-Z0-9_]*)\((%s for %s in %s)\)"
        % (expr, expr, expr))

    content = orig_content
    content = regex_import.sub(replaceImport, content)
    content = regex_call_gen.sub(replaceCallGen, content)
    content = regex_gen.sub(replaceGen, content)
    content = content.replace(" 1 <<", " 1L <<")
#    content = regex_reversed.sub(replaceReversed, content)
    if convert_to != "nofuture" and "yield" in content:
        content = "from __future__ import generators\n%s" % content
except KeyboardInterrupt:
    sys.stderr.write("INTERRUPTED.\n")
    error = True
    content = orig_content
except Exception, err:
    sys.stderr.write("ERROR: %s\n" % err)
    error = True
    content = orig_content
sys.stdout.write(content)
sys.exit(int(error))

