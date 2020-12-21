#!/usr/bin/env python3

import re
import sys


class StringValidator(object):
    INTERPOLATION_PATTERN = re.compile(r'^.*\$[a-zA-Z\{].*$')
    INTERPOLATION_CHARS = {'s', 'f'}

    def __init__(self, filename):
        def _parse_file(f):
            self.lines = [l.strip() for l in f.readlines()]

        if filename == '-':
            _parse_file(sys.stdin)
        else:
            with open(filename, 'rb') as f:
                _parse_file(f)

    def find_strings(self):
        """Scan lines for strings and summarise them"""
        found = []

        curr_string = ''
        open_string = False
        interpolated = None
        last_char = None
        last_non_quote = None
        open_triple = False
        quote_count = 0

        # Find strings semi-intelligently
        for i, line in enumerate(self.lines):
            for c in line:
                if c == '"':
                    quote_count += 1

                    # Looks like the string is being terminated
                    if open_string:
                        if (
                            quote_count == 3 or
                            not open_triple and last_char != '\\'
                        ):
                            # This might be the start of a triple; we'll
                            # decide on the next character
                            if quote_count == 2:
                                continue

                            found.append({
                                'content': curr_string,
                                'interpolated': interpolated,
                                'line_num': i + 1
                            })

                            # Reset values
                            open_string = False
                            curr_string = ''
                            interpolated = None
                            quote_count = 0
                            continue
                    # Looks like a string is starting
                    else:
                        open_triple = quote_count == 3
                        interpolated = (
                            last_char
                            if last_char in self.INTERPOLATION_CHARS else None
                        )
                        open_string = True
                        continue
                else:
                    # Suspected a 3-opener but it was actually just an empty
                    # string. Close it off and add it to the strings now
                    if quote_count == 2:
                        found.append({
                            'content': curr_string,
                            'interpolated': interpolated,
                            'line_num': i + 1
                        })
                        open_string = False
                        curr_string = ''
                        interpolated = None
                        quote_count = 0
                        continue

                    quote_count = 0

                last_char = c

                if open_string:
                    curr_string += c

            if not open_triple:
                open_string = False
                quote_count = 0
                curr_string = ''
                interpolated = None
                last_char = None
            else:
                last_char = '\n'

        return found

    def validate_string(self, details):
        """
        Check if the string found seems to be missing an s (or vice verca)

        :returns: None if valid, reason string if invalid
        """
        seems_interpolated = bool(self.INTERPOLATION_PATTERN.match(
            details['content']
        ))

        if seems_interpolated and not details['interpolated']:
            return (
                'Possible missing s or f on string "{content}", '
                'line {line_num}'
            ).format(details)

        if not seems_interpolated and details['interpolated']:
            return (
                'Possible unneeded {interpolated} on string '
                '{interpolated}"{content}", line {line_num}'
            ).format(details)

        return None

    def run(self):
        found = self.find_strings()

        n = 0
        for s in found:
            error = self.validate_string(s)
            if error:
                n += 1
                print(error)

        if n:
            print('{} string interpolation issues found'.format(n))
        return n


if __name__ == '__main__':
    sys.exit(StringValidator(sys.argv[1]).run())
