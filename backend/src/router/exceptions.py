from displayable_exceptions.http_exception import HTTPServerException
from request.schema import HTTPRequestMethod


class URLNotFound(HTTPServerException):
    def __init__(self, url: str):
        super().__init__(f"URL {url!r} not found")


class HandlerNotFound(HTTPServerException):
    def __init__(self, url: str, method: HTTPRequestMethod):
        super().__init__(f"no handler found for {method.value!r} {url!r}")


class DuplicateRoute(HTTPServerException):
    def __init__(self, path: str, method: HTTPRequestMethod):
        super().__init__(f"{method.value!r} already exists for path {path!r}")


class DuplicateRouter(HTTPServerException):
    def __init__(self):
        super().__init__("router already exists")


class DuplicateRouterPrefix(HTTPServerException):
    def __init__(self, prefix: str):
        super().__init__(f"a router with prefix {prefix!r} already exists")
