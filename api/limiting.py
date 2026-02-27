from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate Limiter Setup (In-memory)
limiter = Limiter(key_func=get_remote_address)

