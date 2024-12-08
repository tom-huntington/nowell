from functools import reduce
from itertools import starmap

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
    "|": "reverse_function_application",
    ".": "b",
    "map": "flipped_map",
    "starmap": "flipped_starmap",
}

def flipped_map(arg0, arg1, *args_):
    *args, func = (arg0, arg1, *args_)
    return map(func, arg0, *args)

def flipped_starmap(arg0, arg1, *args_):
    *args, func = (arg0, arg1, *args_)
    return starmap(func, *args)



def b(*fs_, env=None):
    needed_env = get_needed_env(fs_)
    f, *fs = fs_
    def b_ret(*args):
        def b_inner(v, f_):
            return call_providing_env(f_, v, env=env)
        initial = f(*args)
        return reduce(b_inner, fs, initial)
    
    b_ret.needed_env = needed_env
    return b_ret


def reverse_function_application(arg, func, **kwargs):
    a = getattr(arg, 'needed_env', False)
    f = getattr(arg, 'needed_env', False)
    if not any((a, f)):
        return func(arg, **kwargs)
    elif all(a, f):
        raise NotImplementedError()
    else:
        raise NotImplementedError()
    
    
def read(x):
    return x.read()

def pair(a, b):
    return (a, b)

def flatten(ls):
    return tuple(item for sublist in ls for item in sublist)
