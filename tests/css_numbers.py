"""Finite scalar arithmetic checks for our own CSS declarations.

This is not a CSS parser, unit checker, cascade simulator or browser. Angles
are supplied in radians. Use only on the explicit engine blocks in these tests.
"""
import ast
from functools import lru_cache
import math
import re


def declarations(text):
    result = {}
    for key, value in re.findall(r'--([a-z0-9-]+)\s*:\s*([^;{}]+);', text):
        result.setdefault(key, value)
    return result


@lru_cache(maxsize=1024)
def expression(text):
    text = re.sub(r'(?<=\d)rad\b', '', text)
    text = re.sub(r'var\(--([a-z0-9-]+)(?:,\s*[-.0-9]+)?\)', lambda m:'v_'+m[1].replace('-','_'), text)
    return ast.parse(text, mode='eval').body


def calculate(name, definitions, values):
    memo = dict(values)
    visiting = set()
    def resolve(key):
        if key in memo:return memo[key]
        if key in visiting:raise ValueError('cyclic test declaration')
        visiting.add(key)
        result = visit(expression(definitions[key]))
        visiting.remove(key)
        memo[key] = result
        return result
    def visit(node):
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):return node.value
        if isinstance(node,ast.Name):
            if node.id=='pi':return math.pi
            if node.id.startswith('v_'):return resolve(node.id[2:].replace('_','-'))
        if isinstance(node,ast.UnaryOp):
            value=visit(node.operand)
            if isinstance(node.op,ast.USub):return -value
            if isinstance(node.op,ast.UAdd):return value
        if isinstance(node,ast.BinOp):
            left,right=visit(node.left),visit(node.right)
            if isinstance(node.op,ast.Add):return left+right
            if isinstance(node.op,ast.Sub):return left-right
            if isinstance(node.op,ast.Mult):return left*right
            if isinstance(node.op,ast.Div):return left/right
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and not node.keywords:
            functions={'calc':lambda a:a,'sin':math.sin,'cos':math.cos,'hypot':math.hypot,
                       'atan2':math.atan2,'sign':lambda a:0 if a==0 else math.copysign(1,a),
                       'clamp':lambda low,value,high:max(low,min(value,high)), 'mod':lambda a,b:a%b}
            if node.func.id in functions:return functions[node.func.id](*(visit(a) for a in node.args))
        raise ValueError('unsupported test expression: '+ast.dump(node))
    return resolve(name)
