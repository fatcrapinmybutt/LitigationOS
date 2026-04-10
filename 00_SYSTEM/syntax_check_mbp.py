import ast, sys
src = r"C:\Users\andre\LitigationOS\scripts\themanbearpig.py"
with open(src, encoding="utf-8") as f:
    code = f.read()
try:
    tree = ast.parse(code, filename=src)
    # count classes and methods
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    lines = code.count("\n") + 1
    print(f"SYNTAX OK - {lines} lines, {len(classes)} classes, {len(funcs)} functions")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
    sys.exit(1)
