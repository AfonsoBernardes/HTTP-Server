from displayable_exceptions.http_exception import HTTPServerException
from response.schema import HTTPResponseStatusCode


class InvalidDecoding(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self):
        super().__init__("unable to decode request, make sure it is encoded with UTF-8")


class InvalidRequest(HTTPServerException):
    status_code = HTTPResponseStatusCode.HTTP_400

    def __init__(self):
        super().__init__("invalid request; make sure the request follows HTTP/1.X standards")
