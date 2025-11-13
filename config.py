import os
from datetime import timedelta

class Config:
    # Базовые настройки
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'judo-tournament-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///judo_tournament.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Настройки сессии
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Настройки загрузки файлов
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'

    # Настройки турнира
    DEFAULT_FIGHT_DURATION = 300  # 5 минут в секундах
    GOLDEN_SCORE_DURATION = 180   # 3 минуты золотой скор

    # Возрастные категории (в годах)
    AGE_CATEGORIES = {
        'U10': (8, 10),
        'U12': (10, 12),
        'U14': (12, 14),
        'U16': (14, 16),
        'U18': (16, 18),
        'U21': (18, 21),
        'SENIOR': (18, 35),
        'VETERAN': (35, 100)
    }

    # Весовые категории (мужчины/женщины в кг)
    WEIGHT_CATEGORIES = {
        'MALE': {
            'U60': (0, 60),
            'U66': (60, 66),
            'U73': (66, 73),
            'U81': (73, 81),
            'U90': (81, 90),
            'U100': (90, 100),
            'OVER100': (100, 200)
        },
        'FEMALE': {
            'U48': (0, 48),
            'U52': (48, 52),
            'U57': (52, 57),
            'U63': (57, 63),
            'U70': (63, 70),
            'OVER70': (70, 200)
        }
    }

    # Типы побед
    VICTORY_TYPES = {
        'IPPON': 'Иппон',
        'WAZAARI': 'Ваза-ари',
        'WAZAARI_AWASETE_IPPON': 'Ваза-ари авасетэ иппон',
        'SHIDO': 'Победа по штрафам',
        'HANSOKU_MAKE': 'Хансоку-маке',
        'FUSEN_GACHI': 'Фусэн-гати (неявка)',
        'KIKEN_GACHI': 'Кикэн-гати (отказ)'
    }

    # Роли пользователей
    USER_ROLES = {
        'ADMIN': 'Администратор',
        'REFEREE': 'Судья',
        'SCOREBOARD': 'Табло',
        'VIEWER': 'Зритель'
    }