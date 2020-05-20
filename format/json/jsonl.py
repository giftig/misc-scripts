#!/usr/bin/env python

import json
import sys


def main():
    """Convert a jsonl file into a formatted json file under a "lines" key"""
    lines = []
    with open(sys.argv[1], 'r') as f:
        lines = [json.loads(l) for l in f.readlines() if l]

    print(
        json.dumps(
            {'lines': lines},
            indent=4,
            sort_keys=True
        )
    )

if __name__ == '__main__':
    main()
