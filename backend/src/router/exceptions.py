from displayable_exceptions.displayable_exception import DisplayableException
from request.schema import HTTPRequestMethod


class DuplicateRoute(DisplayableException):
    def __init__(self, route: str, method: HTTPRequestMethod):
        super().__init__(f"{method.value} already exists for route {route!r}")