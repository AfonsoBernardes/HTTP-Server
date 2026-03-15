from enum import Enum


class HTTPProtocol(str, Enum):
    HTTP_1_0 = "HTTP/1.0"
    HTTP_1_1 = "HTTP/1.1"
