import os
import time
import uuid


def uuid7() -> uuid.UUID:
    """UUID v7 (ordenable por tiempo), según RFC 9562."""
    ms = int(time.time() * 1000)
    rnd = int.from_bytes(os.urandom(10), "big")
    valor = (ms & ((1 << 48) - 1)) << 80
    valor |= 0x7 << 76
    valor |= ((rnd >> 62) & 0xFFF) << 64
    valor |= 0b10 << 62
    valor |= rnd & ((1 << 62) - 1)
    return uuid.UUID(int=valor)
