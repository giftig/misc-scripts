#!/usr/bin/env python3
"""
Hacky script to extract data from some JSON:

Pipe a JSON file to this script and provide a line of python code,
referring to the json data as `data`

eg.
$ echo '{"hodor": {"hodor": "hodor!"}}' | \\
>   ./parse-json.py "data['hodor']['hodor']"
hodor!
"""

import json
import sys


def pretty(data):
    if type(data) == str or type(data) == unicode:
        return data

    return json.dumps(data, indent=2, separators=(',', ': '))


if __name__ == '__main__':
    assert len(sys.argv) > 1

    if sys.argv[1] == '--help':
        print(__doc__)
        sys.exit(0)

    with open('/dev/stdin', 'rb') as f:
        data = json.load(f)
        exec('print(pretty({}))'.format(sys.argv[1]))
