from enum import Enum


class HTTPRequestMethod(str, Enum):
    DELETE = "DELETE"
    GET = "GET"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"


class HTTPRequestProtocol(str, Enum):
    HTTP_1_0 = "HTTP/1.0"
    HTTP_1_1 = "HTTP/1.1"
