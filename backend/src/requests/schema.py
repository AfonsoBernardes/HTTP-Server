from enum import Enum


class RequestMethod(str, Enum):
    GET = "GET"
    DELETE = "DELETE"


class RequestProtocol(str, Enum):
    HTTP = "HTTP"
