from . import var_lib
from json_lang import RunningEnv

@var_lib.add_func
def set(run_env: RunningEnv, **kwargs):
    for key, value in kwargs.items():
        run_env.vars[key] = value

@var_lib.add_func
def delete(run_env: RunningEnv, args: list):
    for key in args:
        del run_env.vars[key]
