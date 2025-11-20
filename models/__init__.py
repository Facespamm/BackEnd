"""
Модели данных для системы управления турнирами по дзюдо
"""

from .athlete import Athlete
from .club import Club
from .tournament import Tournament
from .category import Category
from .fight import Fight
from .bracket import Bracket
from .result import Result
from .user import User
from .weighing import Weighing

__all__ = [
    'BaseModel',
    'Athlete',
    'Club', 
    'Tournament',
    'Category',
    'Fight',
    'Bracket',
    'Result',
    'User',
    'Weighing'
]