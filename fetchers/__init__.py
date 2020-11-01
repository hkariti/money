from .utils import FetchException

from . import leumi
from . import leumicard

BACKENDS = {
        'leumi': leumi,
        'leumicard': leumicard
        }

def get_backend(name):
    return BACKENDS[name]
