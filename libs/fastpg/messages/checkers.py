class MSbChecker:
    def __init__(self, MSb: int):
        self.MSb = MSb

    def __eq__(self, code: int):
        return self.MSb == (code >> 16) & 0xFFFF

class LSbChecker:
    def __init__(self, LSb: int):
        self.LSb = LSb

    def __eq__(self, code: int):
        return self.LSb == code & 0xFFFF

class TrueChecker:
    def __init__(self):
        pass
    
    def __eq__(self, value):
        return True

class NoLenTrueChecker:
    def __init__(self):
        pass
    
    def __eq__(self, value):
        return True
