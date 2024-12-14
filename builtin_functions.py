from functools import reduce
from itertools import starmap
from functools import wraps
from collections.abc import Iterable
from operator import eq
from itertools import count
from collections import Counter

def get_needed_env(children):
    return set.union(*(getattr(arg, 'needed_env', set()) for arg in children))
    

def provide_enviroment(args, **kwargs):
    return tuple(arg(**kwargs) if getattr(arg, 'needed_env', False) else arg for arg in args)

def call_providing_env(func, *args, env):
    args = provide_enviroment(args, env=env)
    if getattr(func, 'needed_env', False):
        return func(*args, env=env)
    else:
        return func(*args)

rename_illegal = {
    "&&&": "fanout",
    "***": "parallel",
    "in": "in_",
    # "sorted": "sorted_",
    "not": "not_",
    "|>": "reverse_function_application",
    #"||": "double_reverse_function_application",
    ".": "b",
    "..": "b_curried_w",
    "map": "flipped_map",
    "starmap": "flipped_starmap",
    "filter": "flipped_filter",
    "reduce": "flipped_reduce",
    "<=>": "three_way_compare",
    "==": "eq",
}



def needed_env(func):
    """
    A decorator that calculates `needed_env` for all positional arguments 
    using the `get_needed_env` function and adds it as an attribute 
    to the function's return value.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Call the original function
        needed_env = get_needed_env((*args, func))
        if needed_env:
            def curry_env(env):
                return call_providing_env(func, *args, **kwargs, env=env)
            curry_env.needed_env = needed_env
            return curry_env
        else:
            return func(*args, **kwargs)
    return wrapper

def flipped_map(arg0, arg1, *args_, env=None):
    *args, func = (arg0, arg1, *args_)
    return call_providing_env(map, func, *args, env=env)

def flipped_starmap(arg0, arg1, *args_, env=None):
    *args, func = (arg0, arg1, *args_)
    return call_providing_env(starmap, func, *args, env=env)

def flipped_filter(arg0, arg1, *args_, env=None):
    *args, func = (arg0, arg1, *args_)
    return call_providing_env(filter, func, *args, env=env)


@needed_env
def b(*fs_, env=None):
    #needed_env = get_needed_env(fs_)
    f, *fs = fs_
    def b_ret(*args):
        def b_inner(v, f_):
            return call_providing_env(f_, v, env=env)
        initial = f(*args)
        return reduce(b_inner, fs, initial)
    
    #b_ret.needed_env = needed_env
    return b_ret

@needed_env
def double_reverse_function_application(arg, func, *, env=None):
    closure = call_providing_env(func, arg, env=env)
    return call_providing_env(closure, arg, env=env)

@needed_env
def reverse_function_application(arg, func, env=None):
    return call_providing_env(func, arg, env=env)
    
    
def read(x):
    return x.read()

def pair(a, b):
    return (a, b)

def flatten(ls):
    return tuple(item for sublist in ls for item in sublist)

@needed_env
def W(f, *, env=None):
    def W_r(x):
        return call_providing_env(f, x, x, env=env)
    return W_r

@needed_env
def S(f, g, *, env=None):
    def S_r(x):
        y = call_providing_env(f, x, env=env)
        return call_providing_env(g, x, y, env=env)
    return S_r

@needed_env
def i(x):
    return x

@needed_env
def box(x):
    return [x]

@needed_env
def conditional(pred, true, false):
    def conditional_r(*args):
        if pred(*args):
            return true(*args)
        else:
            return false(*args)
    return conditional_r

@needed_env
def K(x, _):
    return x

@needed_env
def odd(x):
    return x % 2

@needed_env
def even(x):
    return not (x % 2)

@needed_env
def values(xs):
    return xs[1]

@needed_env
def keys(xs):
    return xs[0]

@needed_env
def phi(f, g, h):
    def phi_r(x):
        x_ = f(x)
        y_ = g(x)
        return h(x_, y_)
    return phi_r

@needed_env
def Phi(f, h, g):
    def Phi_r(x):
        x_ = f(x)
        y_ = g(x)
        return h(x_, y_)
    return Phi_r

@needed_env
def split_iterate(acc, func, *, env=None):
    while True:
        acc, r = call_providing_env(func, acc, env=env)
        yield (acc, r)

@needed_env
def iterate(acc, func, *, env=None):
    while True:
        acc = call_providing_env(func, acc, env=env)
        yield acc

@needed_env
def mapAccum(acc, xs, func, env=None):
    res = []
    for x in xs:
        acc, r = call_providing_env(func, acc, x, env=env)
        res.append(r)
    return (acc, res)


@needed_env
def stop_at(it, pred, *, env=None):
   for i in count(0, 1):
       x = next(it)
       print(i, x)
       yield x
       if call_providing_env(pred, x, env=env): return

@needed_env
def not_(x, env=None):
    return not provide_enviroment(x, env=env)


# def step(*, env):
#     def step_r(trails):
#         grid = env["grid"]
#         nines = []
#         new_trails = []
#         for pos, old_height in ((t+dir, grid[t]) for t in trails for dir in [1,-1,1j,-1j]):
#             if grid.get(pos, None) == old_height+1:
#                 if grid.get(pos, None) == 9: nines.append(pos)
#                 else: new_trails.append(pos)
#         return (nines, new_trails)
#     step.needed_env = {"grid"}
#     return step_r

# step.needed_env = {"grid"}

def real(c):
    return c.real

def imag(c):
    return c.imag


def log(x):
    if isinstance(x, Iterable) and not isinstance(x, (str, bytes, Counter)):
        x = list(x)
    print(x)
    return x

@needed_env
def b_curried_w(f, g):
    def b_curried_w_r(x):
        x_ = f(x)
        return g(x_)(x_)
    return b_curried_w_r

@needed_env
def mixed_flatten(xs):
    return tuple(e for el in xs for e in (el if isinstance(el, Iterable) and not  isinstance(el, (str, bytes)) else (el,)))

@needed_env
def take(it, num):
    return tuple(next(it) for _ in range(num))

@needed_env
def last(xs):
    return xs[-1]

@needed_env
def first(xs):
    return xs[0]

@needed_env
def second(xs):
    return xs[1]

# @needed_env
# def scan1(xs, func, *, env=None):
#     for x in xs:
#         yield call_providing_env(func, x, )


@needed_env
def flipped_reduce(xs, func, *, env=None):
    return call_providing_env(reduce, func, xs, env=env)

@needed_env
def excluding_map(xs, func, *, env=None):
    while xs:
        x = next(iter(xs))
        out = set(call_providing_env(func, x, env=env))
        print(out, "---", xs)
        yield out
        xs -= out

@needed_env
def three_way_compare(a, b, env=None):
    return (a > b) - (a < b)

@needed_env
def starfilter(xs, f, env=None):
    return filter(lambda x: f(*x), xs)