import os
from lark import Lark, Transformer, Tree, Token
from lark.visitors import Interpreter
import re
from inspect import signature
from functools import partial
import itertools
from builtin_functions import *
from collections.abc import Iterable
import builtin_functions


with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grammar.lark')) as f:
    grammar = f.read()

parser = Lark(grammar)


def flatten_irregular(xs):
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes, Token)):
            yield from flatten_irregular(x)
        else:
            yield x


def provide_env(tree, env_names):
    if tree.data.value == "closure":
        class Flatten(Transformer):
            def destruct(self, children):
                return flatten_irregular(children)
            
            def IDENT(self, child):
                return child.value
            
            def closure(self, children):
                return flatten_irregular(children[:-1])
            
        # print(tree)
        o = Flatten().transform(tree)
        o_ = list(o)
        new_names = set(o_)
        assert len(new_names) == len(o_)
        env_names = env_names.union(o_)
    
    tree.env_names = env_names
    
    for child in tree.children:
        if isinstance(child, Tree):
            provide_env(child, env_names)
        elif isinstance(child, Token):
            child.value = (child.value, env_names)
    return


class Parser(Transformer):
    def call(self, children):
        #*args, func, final_arg = children
        #args.append(final_arg)
        needed_env = set.union(*(getattr(arg, 'needed_env', set()) for arg in children))
        # needs_env = any(len(env) for env in args.needed_env)
        if needed_env:
            # env -> expr
            def call_r(env):
                *args, func, final_arg = provide_enviroment(children, env=env)
                return func(*args, final_arg)
            call_r.needed_env = needed_env
            return call_r
        else:
            *args, func, final_arg = children
            return func(*args, final_arg)

    # def expr(self, args):
    #     arg, = args
    #     return arg

    ncall = call

    def closure(self, children):
        class ToList(Transformer):
            def destruct(self, children):
                return children
            
            def IDENT(self, child):
                return child.value[0]
        
        *names, body = children
        names, = ToList().transform(Tree("dumy", children[:-1])).children

        needed_env = set.union(*(getattr(arg, 'needed_env', set()) for arg in children))
        
        for name in flatten_irregular(names):
            if name in needed_env:
                needed_env.remove(name)
    
        def closure_r(env={}):
            def closure_rr(*values):
                env_ = dict(env)
                def set_variables(names, values):
                    assert len(names) == len(values)
                    for name, value in zip(names, values):
                        if isinstance(name, list):
                            set_variables(name, value)
                        else:
                            env_[name] = value
                
                set_variables(names, values)
                return body(env=env_) if getattr(body, 'needed_env', False) else body
            return closure_rr
        
        if needed_env:
            closure_r.needed_env = needed_env
            return closure_r
        else:
            return closure_r()
    
    def partial(self, children):
        # for op in (map, starmap):
        #     if op in children and children[0] == op:
        #         children =  tuple(reversed(children))
        #         break

        needed_env = set.union(*(getattr(arg, 'needed_env', set()) for arg in children))
        max_index = not bool(getattr(children[0], '__call__', False))
        # tmp = tuple((len(signature(child.__call__).parameters), i) for i, child in enumerate(children))
        # _, max_index = max(tmp)
        
        if max_index == 1:
            if needed_env:
                def partial1_r(*, env):
                    arg, op = provide_enviroment(children, env=env)
                    return partial(op, arg)
                partial1_r.needed_env = needed_env
                return partial1_r
            else:
                arg, op = children
                return partial(op, arg)
        else:
            op, arg1 = children
            def partial2_r(*, env):
                def partial2_r_inner(*args):
                    arg0, *args2 = args
                    return call_providing_env(op, arg0, arg1, *args2, env=env)
                return partial2_r_inner
            if needed_env:
                partial2_r.needed_env = needed_env
                return partial2_r
            else: return partial2_r(env=None)



    def ident(self, args):
        arg, = args
        value, env_names = arg.value
        value = rename_illegal.get(value, value)

        if value in env_names:
            def indent_r(*, env):
                return env[value]
            indent_r.needed_env = set((value,))
            return indent_r
        else:
            return eval(value)
    
    def FUNCTION(self, arg):
        definition, env_names = arg.value
        # we could support being a capture!!!
        name, = re.match(r'\s+def (.+)\(', definition).groups()

        needed_env = set()
        for n in re.findall(r'\b\w+\b', definition):
            if n in env_names:
                needed_env.add(n)

        if needed_env:
            unpackenv = ''.join(f"{n} = env['{n}']\n" for n in needed_env)
            def indent_block(b : str, times = 1):
                return '    ' + b.replace('\n', '\n' + times * '    ')
            
            closure_ = f"def make_{name}(*, env):\n" + indent_block(unpackenv) + indent_block(definition) + f'\n    return {name}'
            # print(closure_)
            exec(closure_, globals=globals())
            c = eval(f"make_{name}")
            c.needed_env = needed_env
            return Token("FUNCTION", (f"make_{name}", needed_env))
        else:
            exec(definition, globals=globals())
            return Token("FUNCTION", (name, needed_env))




def evaluate_code(ex, args):

    while True:
        if m := re.match(r"^\s*from\s+(\w+)\s+import\s+(\w+)\n", ex):
            # print(f"execing: {m.group()}")
            exec(m.group(), globals())
            ex = ex[m.end():]
        else: break
    
    for tok in parser.lex(ex):
        print(tok.line, tok.column, repr(tok))

    ast = parser.parse(ex)
    print(ast.pretty())
    print(ast)

    provide_env(ast, set())

    program_ = Parser().transform(ast)
    program, = program_.children

    output = call_providing_env(program, *args, env=get_needed_env(program_.children))
    #output = program(env=dict(), *args) if getattr(program, 'is_closure', False) else program(*args)
    return output


def print_iterable(obj):
    if isinstance(obj, (list, tuple, set, dict)):
        print(obj)
    elif hasattr(obj, '__iter__'):
        print(list(obj))
    else:
        print(obj)

code = r"""
ab -> 1 |>
def cap(x):
    return ab


"""

if __name__ == "__main__":
            #(|| (map \a -> \b -> a pair b))
    out = evaluate_code(code, [1])
    print_iterable(out)


