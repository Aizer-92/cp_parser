"""
API routers package
"""

from . import auth
from . import calculator
from . import history
from . import settings

try:
    from . import categories
    __all__ = ['auth', 'calculator', 'history', 'settings', 'categories']
except:
    __all__ = ['auth', 'calculator', 'history', 'settings']