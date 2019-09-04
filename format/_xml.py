#!/usr/bin/env python3
import sys
from xml.dom import minidom

filename = '/dev/stdin'

if len(sys.argv) > 1:
    filename = sys.argv[1]

formatted = minidom.parse(filename).toprettyxml(indent='  ')

# Remove blank lines and trailing whitespace
lines = [
    l.rstrip() for l in formatted.split('\n') if l.strip()
]

print('\n'.join(lines))
