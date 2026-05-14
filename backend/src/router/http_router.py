from typing import Callable, Dict, Optional

from request.schema import HTTPRequestMethod


class HTTPRouter:

    def __init__(self, prefix: Optional[str] = None):
        self.routes = Dict[str, Dict[HTTPRequestMethod, Callable]] = {}
        self.prefix = prefix

    def include_route(self, path: str, method: HTTPRequestMethod, handler: Callable) -> None:
        self.routes[path] = {method: handler}

    # Helper handlers
    def get(self):
        pass

    def _decorator(self, path: str, method: HTTPRequestMethod):
        def _wrapper(handler: Callable) -> Callable:
            pass

        return _wrapper
