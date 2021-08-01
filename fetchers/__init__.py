from .utils import FetchException

from . import leumi
from . import leumicard
from . import cal
from . import recurring

BACKENDS = {
        'leumi': leumi,
        'leumicard': leumicard,
        'cal': cal,
        'recurring': recurring,
        }

def get_backend(name):
    return BACKENDS[name]
