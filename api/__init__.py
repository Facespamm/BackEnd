# Этот файл нужен чтобы Python понимал, что папка api - это пакет
# Можно оставить пустым или импортировать namespace'ы для удобства

from .auth import auth_ns
from .tournaments import tournaments_ns
from .athletes import athletes_ns
from .clubs import clubs_ns
from .fights import fights_ns
from .brackets import brackets_ns
from .results import results_ns
from .weighing import weighing_ns

__all__ = [
    'auth_ns',
    'tournaments_ns',
    'athletes_ns',
    'clubs_ns',
    'fights_ns',
    'brackets_ns',
    'results_ns',
    'weighing_ns'
]