from typing import Callable, Dict, Optional

from request.schema import HTTPRequestMethod
from router.exceptions import DuplicateRoute


class HTTPRouter:

    def __init__(self, prefix: Optional[str] = None):
        self.routes = Dict[str, Dict[HTTPRequestMethod, Callable]] = {}

    def include_route(self, route: str, method: HTTPRequestMethod, handler: Callable) -> None:
        if not self.routes.get(route):
            self.routes[route] = {}

        if method in self.routes[route]:
            raise DuplicateRoute(route, method)

        self.routes[route][method] = handler


    # Helper handlers
    def get(self, route: str) -> Callable:
        return self._decorator(route, HTTPRequestMethod.GET)

    def delete(self, route: str) -> Callable:
        return self._decorator(route, HTTPRequestMethod.DELETE)

    def patch(self, route: str) -> Callable:
        return self._decorator(route, HTTPRequestMethod.PATCH)

    def post(self, route: str) -> Callable:
        return self._decorator(route, HTTPRequestMethod.POST)

    def put(self, route: str) -> Callable:
        return self._decorator(route, HTTPRequestMethod.PUT)

    def head(self, route: str) -> Callable:
        return self._decorator(route, HTTPRequestMethod.HEAD)

    def _decorator(self, route: str, method: HTTPRequestMethod) -> Callable:
        def _wrapper(handler: Callable) -> Callable:
            self.include_route(route, method, handler)
            return handler

        return _wrapper
