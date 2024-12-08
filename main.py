import os
from lark import Lark, Transformer, Tree, Token
from lark.visitors import Interpreter
import re

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grammar.lark')) as f:
    grammar = f.read()

parser = Lark(grammar)

def provide_env(tree, env_names):
    if tree.data.value == "closure":
        env_names = env_names | set(name.value for name in tree.children[:-1])
    
    tree.env_names = env_names
    
    for child in tree.children:
        if isinstance(child, Tree):
            provide_env(child, env_names)
        elif isinstance(child, Token):
            child.value = (child.value, env_names)
    return


# class ProvideEnv(Interpreter):
#     def __default__(self, tree):
#         self.avaliable_names = 
#         return super().__default__(tree)

class Parser(Transformer):
    def call(self, children):
        *args, func, final_arg = children
        args.append(final_arg)
        needed_env = set.union(*(getattr(arg, 'needed_env', set()) for arg in children))
        # needs_env = any(len(env) for env in args.needed_env)
        if needed_env:
            # env -> expr
            def call_r(env):
                a = (arg(env) if getattr(arg, 'needed_env', False) else arg for arg in args)
                if getattr(func, 'needed_env', False):
                    return func(env, *a)
                else:
                    return func(*a)
         
            call_r.needed_env = needed_env
            return call_r
        else:
            return args[-2](*args[:-2], args[-1])

    # def expr(self, args):
    #     arg, = args
    #     return arg

    def closure(self, children):
        *names, body = children
        names = tuple(token.value[0] for token in names)
        needed_env = set.union(*(getattr(arg, 'needed_env', set()) for arg in children))
        
        for name in names:
            if name in needed_env:
                needed_env.remove(name)
        
        def closure_r(env, *values):
            assert len(names) == len(values)
            env.update(zip(names, values))
            return body(env) if getattr(body, 'needed_env', False) else body
        
        closure_r.needed_env = needed_env
        closure_r.is_closure = True
        return closure_r
        

            

    def ident(self, args):
        arg, = args
        value, env_names = arg.value
        if value in env_names:
            def indent_r(env):
                return env[value]
            indent_r.needed_env = set((value,))
            return indent_r
        else:
            return eval(arg)



def evaluate_code(ex, args):

    while True:
        if m := re.match(r"^from\s+(\w+)\s+import\s+(\w+)\n", ex):
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

    program = Parser().transform(ast)
    program, = program.children
    output = program(dict(), *args) if getattr(program, 'is_closure', False) else program(*args)
    return output


def print_iterable(obj):
    if isinstance(obj, (list, tuple, set, dict)):
        print(obj)
    elif hasattr(obj, '__iter__'):
        print(list(obj))
    else:
        print(obj)

if __name__ == "__main__":
    code = """from operator import sub

            a b -> a (c d -> c sub b) b
            """
    out = evaluate_code(code, [1,2])
    print_iterable(out)

