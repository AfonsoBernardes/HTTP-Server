from enum import Enum
from typing import Any


class ContentType(Enum):
    # Text
    PLAIN = "text/plain"
    HTML = "text/html"
    CSS = "text/css"
    JAVASCRIPT = "text/javascript"
    CSV = "text/csv"

    # Application
    JSON = "application/json"
    # XML = "application/xml"
    # FORM_URLENCODED = "application/x-www-form-urlencoded"
    # OCTET_STREAM = "application/octet-stream"
    PDF = "application/pdf"
    ZIP = "application/zip"
    # GRAPHQL = "application/graphql"

    # Multipart
    # FORM_DATA = "multipart/form-data"
    # BYTE_RANGES = "multipart/byteranges"

    # Image
    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    WEBP = "image/webp"
    SVG = "image/svg+xml"

    # # Audio
    # MPEG_AUDIO = "audio/mpeg"
    # OGG_AUDIO = "audio/ogg"
    #
    # # Video
    # MP4 = "video/mp4"
    # WEBM = "video/webm"
    #
    # # Font
    # WOFF = "font/woff"
    # WOFF2 = "font/woff2"
    # TTF = "font/ttf"


class Response:
    content_type: ContentType
    data: Any

    def __init__(self, content_type: ContentType, data: Any) -> None:
        self.content_type = content_type
        self.data = data
