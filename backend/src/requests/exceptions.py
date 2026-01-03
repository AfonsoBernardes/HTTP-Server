from displayable_exceptions.displayable_exception import DisplayableException


class InvalidDecoding(DisplayableException):
    def __init__(self):
        super().__init__("unable to decode request")
