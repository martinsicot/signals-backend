import environ
from .base import *  # noqa: F401, F403

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")  # noqa: F405

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]
