from displayable_exceptions.displayable_exception import DisplayableException
from request.schema import HTTPRequestMethod


class URLNotFound(DisplayableException):
    def __init__(self, url: str):
        super().__init__(f"URL {url!r} not found")


class HandlerNotFound(DisplayableException):
    def __init__(self, url: str, method: HTTPRequestMethod):
        super().__init__(f"no handler found for {method.value!r} {url!r}")


class DuplicateRoute(DisplayableException):
    def __init__(self, route: str, method: HTTPRequestMethod):
        super().__init__(f"{method.value} already exists for route {route!r}")


class DuplicateRouterPrefix(DisplayableException):
    def __init__(self, prefix: str):
        super().__init__(f"a router with prefix {prefix!r} already exists")
