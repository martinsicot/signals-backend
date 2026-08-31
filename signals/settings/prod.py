import environ
from .base import *  # noqa: F401, F403

env = environ.Env()

DEBUG = False

_allowed = env.list("DJANGO_ALLOWED_HOSTS", default=[])
_render_host = env("RENDER_EXTERNAL_HOSTNAME", default="")
ALLOWED_HOSTS = list(filter(None, _allowed + ([_render_host] if _render_host else [])))

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
