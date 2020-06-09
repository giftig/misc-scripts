#!/usr/bin/env python3

import os
import sys

NAMESPACE = os.environ.get('SCALA_PROJECT_NAMESPACE')


def _is_stdlib(s):
    """Imports from stdlib like import scala.concurrent.duration.Duration"""
    prefixes = {
        'java.',
        'javax.',
        'javaw.',
        'scala.'
    }
    for p in prefixes:
        if s.startswith('import ' + p):
            return True

    return False


def _is_project(s):
    """Imports from the current project, like import com.example.foo.Bar"""
    return s.startswith('import ' + NAMESPACE)


def _is_class(s):
    """Imports from a class/object like import DefaultJsonProtocol._"""
    return s.startswith('import ') and len(s) > 7 and s[7].isupper()


def _sort_key(s):
    ignore_braces = s.replace('{', '').replace('}', '')
    underscores_first = ignore_braces.replace('_', '@')
    return underscores_first


def rewrite_file(ff):
    print('Rewriting {}...'.format(ff))

    data = []
    with open(ff, 'r') as f:
        data = f.readlines()

    stdlib_imports = []
    third_party_imports = []
    project_imports = []
    class_imports = []

    continuation = False  # Multi-line import (brace left unclosed)
    i = None

    imports_stripped = []

    for line in data:
        if continuation:
            i += line

            if '}' in line:
                continuation = False
            else:
                continue
        else:
            i = line

        if not i.startswith('import'):
            imports_stripped.append(i)
            continue

        if '{' in line and '}' not in line:
            continuation = True
            continue

        if _is_stdlib(i):
            stdlib_imports.append(i)
        elif _is_project(i):
            project_imports.append(i)
        elif _is_class(i):
            class_imports.append(i)
        else:
            third_party_imports.append(i)

    stdlib_imports.sort(key=_sort_key)
    third_party_imports.sort(key=_sort_key)
    project_imports.sort(key=_sort_key)
    class_imports.sort(key=_sort_key)

    for import_list in [
        stdlib_imports,
        third_party_imports,
        project_imports,
        class_imports
    ]:
        if import_list:
            import_list.insert(0, '\n')

    all_imports = (
        stdlib_imports +
        third_party_imports +
        project_imports +
        class_imports +
        ['\n']
    )

    patched = []
    found_body = False

    # Strip blank lines until we encounter a non-blank line which
    # doesn't start with 'package', and then insert our reformatted imports
    # into this space
    for l in imports_stripped:
        if found_body or l.startswith('package'):
            patched.append(l)
            continue

        if not l.strip():
            continue

        patched.extend(all_imports)
        found_body = True

        patched.append(l)

    with open(ff, 'w') as f:
        f.writelines(patched)


def main():
    if len(sys.argv) <= 1:
        print('Filenames to rewrite required')
        sys.exit(1)

    if not NAMESPACE:
        print(
            'You must provide a namespace via the SCALA_PROJECT_NAMESPACE'
            'environment variable'
        )

    print('Own project namespace: {}'.format(NAMESPACE))
    for f in sys.argv[1:]:
        rewrite_file(f)


if __name__ == '__main__':
    main()
