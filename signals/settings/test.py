import environ
from pathlib import Path

environ.Env.read_env(Path(__file__).resolve().parent.parent.parent / ".env")

from .base import *  # noqa: F401, F403

DEBUG = False
ALLOWED_HOSTS = ["*"]

# Désactive l'enregistrement des requêtes SQL en mémoire
DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405

# Hasheur de mot de passe rapide pour les tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Désactive les emails réels
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Désactive Celery (tâches synchrones)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
