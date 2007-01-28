#!/bin/sh

# Use Olivier Grisel "trace2html" tool to do coverage test
# Create HTML report in coverage_report/ directory
#
# http://cheeseshop.python.org/pypi/trace2html

trace2html.py -w hachoir_core -w hachoir_parser -w hachoir_metadata -o coverage_report --run-command coverage_test.py
