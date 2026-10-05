"""Rate limiting configuration for the application.

This module configures rate limiting using slowapi, with default limit
defined in the application settings. Rate limit are applied based on
remote IP addresses.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from config.settings import settings

limiter = Limiter(key_func=get_remote_address, default_limits=settings.RATE_LIMIT_DEFAULT)
