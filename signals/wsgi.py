import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "signals.settings.prod")

application = get_wsgi_application()

# Serve committed catalog media (product images) through WhiteNoise.
# Render has no persistent disk, so product images are shipped inside the
# image at MEDIA_ROOT/products/ and served here under MEDIA_URL. WhiteNoise
# already serves STATIC_ROOT via its middleware; this only adds the media dir.
from whitenoise import WhiteNoise  # noqa: E402

# max_age: catalog images change rarely; cache for a day (filenames are not
# content-hashed, so keep it modest enough that corrections propagate quickly).
application = WhiteNoise(application, max_age=86400)
application.add_files(str(settings.MEDIA_ROOT), prefix=settings.MEDIA_URL)
