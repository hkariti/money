from .utils import FetchException

from . import leumi
from . import leumicard
from . import cal
from . import recurring
from . import otsar

BACKENDS = {
        'leumi': leumi,
        'leumicard': leumicard,
        'cal': cal,
        'recurring': recurring,
        'otsar': otsar,
        }

def get_backend(name):
    return BACKENDS[name]
