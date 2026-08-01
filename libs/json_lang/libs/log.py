from . import log_lib

@log_lib.add_func(func_name="print")
def log_print(args: list):
    print(*args)
