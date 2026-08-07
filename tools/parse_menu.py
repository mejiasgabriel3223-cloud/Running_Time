import ast, traceback

path = 'menu.py'
try:
    src = open(path, encoding='utf-8').read()
    ast.parse(src)
    print('AST parse OK')
except SyntaxError as e:
    print('SyntaxError:')
    print('  msg:', e.msg)
    print('  lineno:', e.lineno)
    print('  offset:', e.offset)
    if e.text:
        print('  text:', repr(e.text))
    traceback.print_exc()
except Exception:
    traceback.print_exc()
