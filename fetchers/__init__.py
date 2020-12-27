from .utils import FetchException

from . import leumi
from . import leumicard
from . import cal

BACKENDS = {
        'leumi': leumi,
        'leumicard': leumicard,
        'cal': cal,
        }

def get_backend(name):
    return BACKENDS[name]
