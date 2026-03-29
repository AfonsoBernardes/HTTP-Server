from displayable_exceptions.displayable_exception import DisplayableException


class InvalidDecoding(DisplayableException):
    def __init__(self):
        super().__init__("unable to decode request")


class InvalidRequest(DisplayableException):
    def __init__(self):
        super().__init__("invalid request; make sure the request follows HTTP/1.X standards")
