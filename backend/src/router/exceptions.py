from displayable_exceptions.http_exception import HTTPServerException, DisplayableException
from request.schema import HTTPRequestMethod
from response.schema import HTTPResponseStatusCode


class URLNotFound(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_404

    def __init__(self, url: str):
        super().__init__(f"URL {url!r} not found")


class HandlerNotFound(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_405

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
