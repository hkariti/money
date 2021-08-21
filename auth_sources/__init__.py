from .base import AuthError

from . import bitwarden

BACKENDS = {
        'bitwarden': bitwarden.BitWardenAuthSource,
        }

def get_backend(name):
    return BACKENDS[name]
