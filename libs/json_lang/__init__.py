from typing import Callable
from typing import Optional
from .var_utils import VarUtils
import inspect

class Lib:
    def __init__(self, name: str):
        self.func_list: dict[str, Callable] = dict()
        self.name = name

    def add_func(self, func: Optional[Callable] = None, func_name: Optional[str] = None):
        if callable(func):
            self.func_list[func.__name__ if func_name is None else func_name] = func
            return func
        
        def decorator(func):
            self.func_list[func.__name__ if func_name is None else func_name] = func
            return func
        return decorator

    def get_func(self, func_name):
        return self.func_list[func_name]

class RunningEnv:
    def __init__(self, lib_list: dict[str, Lib], init_vars: dict, lib_only_vars: dict):
        self.lib_list: dict[str, Lib] = lib_list
        self.vars = VarUtils(init_vars)
        self.lib_only_vars = lib_only_vars
    
    def get_func(self, func_str: str):
        lib_func = func_str.split(".")
        return self.lib_list[lib_func[0]].get_func(lib_func[1])
    
    def perform(self, instructions: list):
        for instruction in instructions:
            for func_name, params in instruction.items():
                func = self.get_func(func_name)
                sig = inspect.signature(func)

                kwargs = self.vars.get_var_args(params.get("kwargs", {}))
                args = self.vars.get_var_args(params.get("args", []))

                for name, param in sig.parameters.items():
                    if param.annotation == type(self):
                        kwargs[name] = self
                    elif name == "args" and param.annotation is list:
                        kwargs["args"] = args

                res = func(**kwargs)

                if params.get("write_to") is not None:
                    self.vars[params["write_to"]] = res

class LibReg:
    def __init__(self):
        self.lib_list: dict[str, Lib] = dict()

    def new_run(self, init_vars: dict, lib_only_vars: dict):
        return RunningEnv(self.lib_list, init_vars, lib_only_vars)

    def add_lib(self, lib: Lib):
        self.lib_list[lib.name] = lib

if __name__ == "__main__":
    test_lib = Lib("lib")

    @test_lib.add_func
    def some_func():
        print("test")

    @test_lib.add_func()
    def new_func():
        print("new")

    @test_lib.add_func(func_name="last")
    def last_testing_func(env: RunningEnv, args: list):
        print(f"{args}: {env.vars}")

    print(test_lib.func_list)
    print(test_lib.name)

    libs = LibReg()
    libs.add_lib(test_lib)

    run = libs.new_run({"test": 123}, {"lib_only": "something"})
    insts = {
    "intructions": [
        {"lib.some_func": {"kwargs": {}, "args": [], "write_to": None}},
        {"lib.last": {"kwargs": {}, "args": ["hello"], "write_to": None}}
    ]
}
    run.perform(insts["intructions"])
