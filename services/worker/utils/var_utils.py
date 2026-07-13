from typing import Any


class VarUtils:
    def __init__(self, vars: dict):
        self.vars: dict = vars
    
    def __str__(self):
        return str(self.vars)
    
    def read_variable(self, string: str) -> str:
        if "V:{" not in string:
            return string
        start_i: int = int()
        end_i: int = int()
        i_sequence_updated: int = int()
        sequence: str = str()
        var_i_s: list[list[int, int]] = list()
        for i in range(len(string)):
            if sequence == "V:{" and string[i] == "}":
                end_i = i
                var_i_s.append([start_i, end_i])
                i_sequence_updated = i
                sequence = str()
            if (string[i] == "V" and sequence == "") or (string[i] == ":" and sequence == "V") or (string[i] == "{" and sequence == "V:") and (i_sequence_updated+1 == i):
                i_sequence_updated = i
                sequence = sequence + string[i]
                if sequence == "V:{":
                    start_i = i+1
            elif i_sequence_updated+1 != i and sequence != "V:{":
                i_sequence_updated = i
                sequence = str()
        full_var_string: str = str()
        for i in range(len(var_i_s)):
            var_name = string[var_i_s[i][0]:var_i_s[i][1]]
            var_args = var_name.split(".")
            var_args.pop(0)
            var_name = var_name.split(".")[0]
            var_value = self.vars[var_name]
            for arg in var_args:
                var_value = getattr(var_value, arg)
            if i == 0 and len(var_i_s)-1 == i:
                full_var_string = full_var_string + string[:var_i_s[i][0]-3] + var_value + string[var_i_s[i][1]+1:]
            elif i != 0 and len(var_i_s)-1 == i:
                full_var_string = full_var_string + var_value + string[var_i_s[i][1]+1:]
            elif i == 0 and len(var_i_s)-1 != i:
                full_var_string = full_var_string + string[:var_i_s[i][0]-3] + var_value + string[var_i_s[i][1]+1:var_i_s[i+1][0]-3]
            elif i != 0 and len(var_i_s)-1 != i:
                full_var_string = full_var_string + var_value + string[var_i_s[i][1]+1:var_i_s[i+1][0]-3]
        return full_var_string

    def get_var_args(self, args: list | dict) -> list | dict:
        if isinstance(args, list):
            var_args: list = list()
            for arg in args:
                var_arg = self.read_variable(arg) if isinstance(arg, str) else self.get_var_args(arg)
                var_args.append(var_arg if var_arg is not None else arg)
            return var_args
        elif isinstance(args, dict):
            var_kwargs: dict = dict()
            for key, arg in args.items():
                var_arg = self.read_variable(arg) if isinstance(arg, str) else self.get_var_args(arg)
                var_kwargs[key] = var_arg
            return var_kwargs
        elif args is None:
            return None
    
    def __getitem__(self, name: str) -> Any:
        try:
            return self.vars[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setitem__(self, name: str, value: Any) -> None:
        self.vars[name] = value
    
    def __delitem__(self, name: str) -> None:
        try:
            del self.vars[name]
        except KeyError:
            raise AttributeError(name) from None

if __name__ == "__main__":
    class Test:
        def __init__(self):
            self.test = "b"
    vars = VarUtils({"var1": "a", "var": Test()})
    print(f"read_variable test: {vars.read_variable("/hfV: {V:{var.test}/1f}}f23/a/V:{var1}") == "/hfV: {b/1f}}f23/a/a"}")
    print(f"""get_var_args test: {vars.get_var_args([
            "videos", 
            {
                "title": "V:{var.test}", 
                "description": "V:{var1}", 
                "author_user_id": "V:{var.test}"
            },
            "video"
            ]) == ['videos', {'title': 'b', 'description': 'a', 'author_user_id': 'b'}, 'video']}""")
    vars["var2"] = "abc"
    print(vars)
