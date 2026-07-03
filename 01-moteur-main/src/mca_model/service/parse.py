import ast
import inspect

from typing import Callable




def function_calls_and_expr(func:Callable):
    """!! fonction générée, bugs possibles"""
    src = inspect.getsource(func)
    tree = ast.parse(src)

    calls = set()
    expr_str = None

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            self.generic_visit(node)

    visitor = Visitor()

    # find the function definition
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            for stmt in node.body:
                if isinstance(stmt, ast.Return):
                    visitor.visit(stmt)
                    
                    # reconstruct source code of the returned expression
                    expr_str = ast.unparse(stmt.value)  # type: ignore

            
    return {
        'functions called':calls,
        'expression':  expr_str}
