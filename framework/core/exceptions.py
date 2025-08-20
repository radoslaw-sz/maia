class MaiaAssertionError(AssertionError):
    def __init__(self, message, result=None):
        super().__init__(message)
        self.result = result
