from displayable_exceptions.displayable_exception import DisplayableException
from request.schema import HTTPRequestMethod
from router.http_router import HTTPRouter


class URLNotFound(DisplayableException):
    def __init__(self, url: str):
        super().__init__(f"URL {url!r} not found")


class HandlerNotFound(DisplayableException):
    def __init__(self, url: str, method: HTTPRequestMethod):
        super().__init__(f"no handler found for {method.value!r} {url!r}")


class DuplicateRoute(DisplayableException):
    def __init__(self, path: str, method: HTTPRequestMethod):
        super().__init__(f"{method.value!r} already exists for path {path!r}")

class DuplicateRouter(DisplayableException):
    def __init__(self):
        super().__init__("router already exists")


class DuplicateRouterPrefix(DisplayableException):
    def __init__(self, prefix: str):
        super().__init__(f"a router with prefix {prefix!r} already exists")
