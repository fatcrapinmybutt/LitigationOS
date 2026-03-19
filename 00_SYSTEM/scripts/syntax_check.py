import ast
import sys

files = [
    r'C:\Users\andre\scans\tooling\config.py',
    r'C:\Users\andre\scans\tooling\phase14_finalize.py',
    r'C:\Users\andre\scans\tooling\phase15_validation.py'
]

errors_found = False
for f in files:
    try:
        with open(f) as fp:
            ast.parse(fp.read())
        print(f'{f.split(chr(92))[-1]} OK')
    except SyntaxError as e:
        print(f'{f}: SYNTAX ERROR')
        print(f'  Line {e.lineno}: {e.msg}')
        if e.text:
            print(f'  {e.text}')
        print(f'  {" " * (e.offset - 1 if e.offset else 0)}^')
        errors_found = True
    except Exception as e:
        print(f'{f}: ERROR - {e}')
        errors_found = True

if not errors_found:
    print('\nAll files passed syntax validation!')
