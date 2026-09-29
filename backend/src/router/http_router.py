from typing import Callable, Dict

from request.http_request import HTTPRequest
from request.schema import HTTPRequestMethod
from response.http_response import HTTPResponse
from router.exceptions import DuplicateRoute, HandlerNotFound, PathNotFound


class HTTPRouter:

    def __init__(self):
        self.routes: Dict[str, Dict[HTTPRequestMethod, Callable]] = {}

    def include_route(self, path: str, method: HTTPRequestMethod, handler: Callable) -> None:
        self.routes.setdefault(path, {})

        if method in self.routes[path]:
            raise DuplicateRoute(path, method)

        self.routes[path][method] = handler

    def resolve(self, path: str, method: HTTPRequestMethod) -> Callable[[HTTPRequest], HTTPResponse]:
        route = self.routes.get(path)
        if not route:
            raise PathNotFound(path)

        handler = route.get(method)
        if not handler:
            raise HandlerNotFound(path, method)

        return handler

    # Helper handlers
    def get(self, path: str) -> Callable:
        return self._decorator(path, HTTPRequestMethod.GET)

    def delete(self, path: str) -> Callable:
        return self._decorator(path, HTTPRequestMethod.DELETE)

    def patch(self, path: str) -> Callable:
        return self._decorator(path, HTTPRequestMethod.PATCH)

    def post(self, path: str) -> Callable:
        return self._decorator(path, HTTPRequestMethod.POST)

    def put(self, path: str) -> Callable:
        return self._decorator(path, HTTPRequestMethod.PUT)

    def head(self, path: str) -> Callable:
        return self._decorator(path, HTTPRequestMethod.HEAD)

    def _decorator(self, path: str, method: HTTPRequestMethod) -> Callable:
        def _wrapper(handler: Callable) -> Callable:
            self.include_route(path, method, handler)
            return handler

        return _wrapper
