#!/usr/bin/env python3

import os
import sys

NAMESPACE = os.environ.get('SCALA_PROJECT_NAMESPACE', 'com.example')

def _is_stdlib(s):
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
    return s.startswith('import ' + NAMESPACE)


def rewrite_file(ff):
    print('Rewriting {}...'.format(ff))

    data = []
    with open(ff, 'r') as f:
        data = f.readlines()

    stdlib_imports = []
    third_party_imports = []
    project_imports = []

    for i in data:
        if not i.startswith('import'):
            continue

        if _is_stdlib(i):
            stdlib_imports.append(i)
        elif _is_project(i):
            project_imports.append(i)
        else:
            third_party_imports.append(i)

    stdlib_imports.sort()
    third_party_imports.sort()
    project_imports.sort()

    for import_list in [stdlib_imports, third_party_imports, project_imports]:
        if import_list:
            import_list.insert(0, '\n')

    all_imports = (
        stdlib_imports +
        third_party_imports +
        project_imports +
        ['\n']
    )

    imports_stripped = [l for l in data if not l.startswith('import')]
    patched = []
    found_body = False

    # Strip blank lines until we encounter a non-blank line which
    # doesn't start with 'package', and then insert out reformatted imports
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

    print('Own project namespace: {}'.format(NAMESPACE))
    for f in sys.argv[1:]:
        rewrite_file(f)


if __name__ == '__main__':
    main()
