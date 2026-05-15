from typing import Callable, Dict, Optional

from request.schema import HTTPRequestMethod
from router.exceptions import DuplicateRoute, URLNotFound, HandlerNotFound


class HTTPRouter:

    def __init__(self, prefix: Optional[str] = None):
        self.routes = Dict[str, Dict[HTTPRequestMethod, Callable]] = {}

    def include_route(self, path: str, method: HTTPRequestMethod, handler: Callable) -> None:
        if not self.routes.get(path):
            self.routes[path] = {}

        if method in self.routes[path]:
            raise DuplicateRoute(path, method)

        self.routes[path][method] = handler

    def resolve(self, url: str, method: HTTPRequestMethod) -> None:
        route = self.routes.get(url)
        if not route:
            raise URLNotFound(url)

        handler = route.get(method)
        if not handler:
            raise HandlerNotFound(url, method)


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
