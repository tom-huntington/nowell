from functools import reduce
from itertools import starmap
from functools import wraps

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
    "map": "flipped_map",
    "starmap": "flipped_starmap",
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
        needed_env = get_needed_env(args)
        if needed_env:
            def curry_env(env):
                return func(*args, **kwargs, env=env)
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
def S(f, *, env=None):
    def S_r(x):
        return call_providing_env(f, x, x, env=env)
    return S_r
