from dataclasses import dataclass


@dataclass(frozen=True)
class ServerLimits:
    max_body_size: int = 1 * 1024 * 1024


DEFAULT_LIMITS = ServerLimits()
