from enum import IntEnum

from response.exceptions import InvalidHTTPStatusCode

HTTP_STATUS_MESSAGES = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    103: "Early Hints",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    226: "IM Used",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",
    421: "Misdirected Request",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required",
}


class HTTPResponseStatusCode(IntEnum):
    # --- Informational responses (100–199) ---
    HTTP_100 = 100
    HTTP_101 = 101
    HTTP_102 = 102
    HTTP_103 = 103

    # --- Successful responses (200–299) ---
    HTTP_200 = 200
    HTTP_201 = 201
    HTTP_202 = 202
    HTTP_203 = 203
    HTTP_204 = 204
    HTTP_205 = 205
    HTTP_206 = 206
    HTTP_207 = 207
    HTTP_208 = 208
    HTTP_226 = 226

    # --- Redirection messages (300–399) ---
    HTTP_300 = 300
    HTTP_301 = 301
    HTTP_302 = 302
    HTTP_303 = 303
    HTTP_304 = 304
    HTTP_305 = 305
    HTTP_307 = 307
    HTTP_308 = 308

    # --- Client error responses (400–499) ---
    HTTP_400 = 400
    HTTP_401 = 401
    HTTP_402 = 402
    HTTP_403 = 403
    HTTP_404 = 404
    HTTP_405 = 405
    HTTP_406 = 406
    HTTP_407 = 407
    HTTP_408 = 408
    HTTP_409 = 409
    HTTP_410 = 410
    HTTP_411 = 411
    HTTP_412 = 412
    HTTP_413 = 413
    HTTP_414 = 414
    HTTP_415 = 415
    HTTP_416 = 416
    HTTP_417 = 417
    HTTP_418 = 418
    HTTP_421 = 421
    HTTP_422 = 422
    HTTP_423 = 423
    HTTP_424 = 424
    HTTP_425 = 425
    HTTP_426 = 426
    HTTP_428 = 428
    HTTP_429 = 429
    HTTP_431 = 431
    HTTP_451 = 451

    # --- Server error responses (500–599) ---
    HTTP_500 = 500
    HTTP_501 = 501
    HTTP_502 = 502
    HTTP_503 = 503
    HTTP_504 = 504
    HTTP_505 = 505
    HTTP_506 = 506
    HTTP_507 = 507
    HTTP_508 = 508
    HTTP_510 = 510
    HTTP_511 = 511

    @property
    def status_message(self):
        try:
            status_message = HTTP_STATUS_MESSAGES[self.value]
        except KeyError:
            raise InvalidHTTPStatusCode(self.value)
        return status_message

    def __str__(self):
        return f"{self.value} {self.status_message}"
