from dataclasses import dataclass


@dataclass(frozen=True)
class ServerLimits:
    max_body_size: int = 10 * 1024**2  # 10 MB
    max_chunk_size: int = 5 * 1024**2  # 5 MB
    max_chunk_size_line_length: int = 4 * 1024  # 4 KB for size + extensions
    max_chunk_count: int = 100_000  # avoid many tiny chunks


DEFAULT_LIMITS = ServerLimits()
