.PHONY: clean doc checkroot

PYTHONVER=2.4
PYTHON=python$(PYTHONVER)
REST2HTML=rst2html   # included in Python docutils
export PYTHON PYTHONVER
XGETTEXT=xgettext
MSGFMT=msgfmt

DOC_SOURCES=$(wildcard doc/*.txt)
DOC_HTML=$(patsubst %.txt,%.html,$(DOC_SOURCES))
CSS="rest.css"
VERSION=$(shell $(PYTHON) ./get_version.py)
PYLINT_OPT =--function-rgx="_?[a-z][a-zA-Z0-9]+"
PYLINT_OPT+=--method-rgx="_{0,2}[a-z][a-zA-Z0-9]+"
PYLINT_OPT+=--class-rgx="[A-Z][a-zA-Z0-9]+"

# --no-classattr: No "No class attribute (XXX) found"
# --exec: Warn about use of --exec
# --stdlib: Ignore stdlib errors
# --no-returnvalues: Ignore "Function return types are inconsistent"
PYCHECKER_OPT=--no-classattr --exec --stdlib --no-returnvalues

ROOT_DIR=$(PWD)
EPYDOC_OPT=--html -n "Hachoir" -u "http://hachoir.org/"
API_DIR=$(shell cd doc; pwd)/api

# Translation (i18n)
PACKAGE=hachoir-core
POT=locale/$(PACKAGE).pot
LANGUAGES=$(patsubst %.po,%,$(shell cd locale; ls *.po))
SOURCES=$(wildcard hachoir_core/*.py hachoir_core/stream/*.py hachoir_core/parser/program/python.py)

WIKI2TXT= s/\r$$//;			\
if (/^{{{/) {				\
	$$indent = "\t";		\
} elsif (/^}}}/) {			\
	$$indent = "";			\
}					\
if (/^(  )* 1. /) {			\
	my $$j = $$_;			\
	$$j =~ s/^((  )*).*/$$1/;	\
	$$j = length($$j) >> 1;		\
	@i = @i[0..$$j];		\
	$$i[$$j]++;			\
	s/^((  )*) 1. /$$1 $$i[$$j]. /;	\
} else {				\
	@i = 0;				\
}					\
s/'\'\'\''?|{{{|}}}//g;			\
s/!([A-Z]\w+)/$$1/g;			\
					\
s/^(.)/$$indent$$1/;

.PHONY: INSTALL

all:
	@echo "Hachoir version $(VERSION)"
	@echo
	@echo "[compile & install]"
	@echo "  make install - install hachoir-core"
	@echo "  make doc - create HTML documentation (from reST text)"
	@echo "  make api - create API HTML documentation (using epydoc)"
	@echo "  make egg - build an egg (then list dist/ directory)"
	@echo "  make win32 - build win32 package (then list dist/ directory)"
	@echo "  make uninstall - (try to) uninstall hachoir-core"
	@echo "  make clean - remove all useless files"
	@echo
	@echo "[tests]"
	@echo "  make test - run all tests"
	@echo "  make test-unittest - run unit tests"
	@echo "  make test-doc - run documentation tests"
	@echo "  make test-setup - test setup.py"
	@echo
	@echo "[static code analys]"
	@echo "  make pylint - run pylint on source code"
	@echo
	@echo "[i18n]"
	@echo "  make pot - create .po template"
	@echo "  make mo  - compile .po files into .mo and create locale/ tree"

checkroot:
	@if test $(shell id -u) -ne 0; then \
		echo "You have to be root (use su or sudo)"; \
		exit 1; \
	fi

prepare-install: INSTALL
install: prepare-install checkroot
	./setup.py install

uninstall: checkroot
	@set -x; \
    rm -rf /usr/lib/python$(PYTHONVER)/site-packages/hachoir-core-$(VERSION)-py2.4.egg;

doc: $(DOC_HTML)
	@echo "Documentation updated."

%.html: %.txt
	@echo "Compile documentation $<"
	@$(REST2HTML) <$< >$@ --stylesheet=$(CSS) --link-stylesheet || { rm -f $@; exit 1; }

egg: prepare-install
	./setup.py sdist bdist_egg

win32: prepare-install
	#./setup.py bdist_wininst
	#./setup.py bdist --format=wininst
	./setup.py bdist_msi

test: test-unittest test-doc test-setup
	@echo "End of tests."

test-unittest:
	@echo "[run unit tests]"
	@$(PYTHON) run_unit_test.py && echo

test-doc:
	@echo "[test using documentation]"
	@$(PYTHON) test_doc.py && echo

test-setup:
	@echo "[test setup.py]"
	@$(PYTHON) setup.py test && echo

pylint:
	@echo "Run pylint on hachoir_core/*.py"
	@PYTHONPATH=$(ROOT_DIR) pylint $(PYLINT_OPT) $(shell find hachoir_core/ -name "*.py" ! -name "__init__.py")

pychecker: pychecker-root pychecker-field pychecker-stream pychecker-parser
pychecker-root:
	@echo "Run pychecker on hachoir_core/*.py"
	@(cd hachoir_core; \
		PYTHONPATH=$(ROOT_DIR) pychecker $(PYCHECKER_OPT) $(shell ls *.py|grep -v compatibility))
pychecker-field:
	@echo "Run pychecker on hachoir_core/field/*.py"
	@(cd hachoir_core/field; \
		PYTHONPATH=$(ROOT_DIR) pychecker $(PYCHECKER_OPT) *.py)
pychecker-parser:
	@echo "Run pychecker on parsers"
	@(cd hachoir_core/parser; \
		PYTHONPATH=$(ROOT_DIR) pychecker $(PYCHECKER_OPT) $(shell cd $(ROOT_DIR)/hachoir_core/parser; find -name "*.py"|grep -v init|grep -v template))
pychecker-stream:
	@echo "Run pychecker on hachoir_core/stream/*.py"
	@(cd hachoir_core/stream; \
		PYTHONPATH=$(ROOT_DIR) pychecker $(PYCHECKER_OPT) *.py)

clean:
	find \( -name "*.pyc" -o -name "*.pyo" -o -name "*.class" -o -name "*.orig" -o -name "*.rej" \) -print0 | xargs -0 rm -f
	find doc -name "*.html" -print0 | xargs -0 rm -f
	rm -rf dist build hachoir_core.egg-info doc/api $(POT) INSTALL
	rm -rf {gettext,distutils,textwrap,optparse,datetime}.py # downloaded for compatibility
	(cd locale && rm -rf $(LANGUAGES))

api:
	test -e $(API_DIR) || mkdir -p $(API_DIR)
	(cd $(ROOT_DIR) && epydoc $(EPYDOC_OPT) -o $(API_DIR) hachoir_core)

mo:
	@for lang in $(LANGUAGES); do \
	    echo "Compile language $$lang"; \
		LOCALE=locale/$$lang/LC_MESSAGES; \
		mkdir -p $$LOCALE && $(MSGFMT) locale/$$lang.po -o $$LOCALE/$(PACKAGE).mo; \
	done

pot: $(POT)
$(POT): $(SOURCES)
	$(XGETTEXT) -o $(POT) --keyword=_u --keyword=ungettext --language=Python $(SOURCES)

INSTALL:
	@echo -n "Create INSTALL: "
	@wget -qO - 'http://hachoir.org/wiki/Install?format=txt' | \
		perl -pe '$(WIKI2TXT)' | fmt -sw80 > INSTALL
	@echo "ok"

