from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
import openam

try:
    OPENAM_ENDPOINT = settings.OPENAM_ENDPOINT
except AttributeError:
    raise ImproperlyConfigured("You must set OPENAM_ENDPOINT in the application's settings")

try:
    session_header_name = settings.OPENAM_SESSION_HEADER_NAME
except AttributeError:
    raise ImproperlyConfigured("You must set OPENAM_SESSION_HEADER_NAME in the application's settings")

user_model = get_user_model()

OPENAM_DJANGO_ATTRIBUTES_MAP = (
    ('givenName', 'first_name'),
    ('sn', 'last_name'),
    ('mail', 'email')
)

class OpenAMJSONBackend(object):
    """
    Uses python-openam to authenticate against an openam server using the
    OpenAM json API
    """

    supports_inactive_user = False

    def authenticate(self, username=None, password=None):

        oam = openam.OpenAM(OPENAM_ENDPOINT,
                session_header_name=session_header_name)
        username = username.lower()

        try:
            token = oam.authenticate(username, password)
            attrs = oam.attributes(token, username)

            user, _ = user_model.objects.get_or_create(username=username)

            # update Django user attrs
            for oam_att, django_att in OPENAM_DJANGO_ATTRIBUTES_MAP:
                if hasattr(user, django_att) and attrs.get(oam_att, None):
                    val = attrs.get(oam_att)
                    if not isinstance(val, basestring):
                        val = val[0]
                    setattr(user, django_att, val)

            user.save()
            return user
        except (openam.AuthenticationFailure, openam.OpenAMError) as e:
            return None


    def get_user(self, username):
        try:
            username_lower = username.lower()
        except AttributeError:
            username_lower = username
        try:
            return user_model.objects.get(pk=username_lower)
        except user_model.DoesNotExist:
            return None
