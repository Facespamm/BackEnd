import os
from datetime import timedelta# Базовые настройки
SECRET_KEY = os.environ.get('SECRET_KEY') or 'judo-tournament-secret-key-2024'

# Остальные настройки без изменений...
PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
UPLOAD_FOLDER = 'static/uploads'
DEFAULT_FIGHT_DURATION = 240  # 4 минуты в секундах
GOLDEN_SCORE_DURATION = 180   # 3 минуты в секундах

# Опции времени боя (в минутах)
FIGHT_TIME_OPTIONS = [2, 3, 4]

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

# Типы оценок (по правилам дзюдо IJF)
SCORE_TYPES = {
    'IPPON': 'Иппон',
    'WAZAARI': 'Ваза-ари',
    'YUKO': 'Юко',
    'WAZAARI_AWASETE_IPPON': 'Два ваза-ари = иппон'
}

# Баллы за каждую оценку
SCORE_VALUES = {
    'YUKO': 1,
    'WAZAARI': 2,
    'IPPON': 10
}

# Время осаекоми для оценок (в секундах)
OSAEKOMI_TIMES = {
    'WAZAARI': 10,    # 10-19 секунд = ваза-ари
    'IPPON': 20       # 20+ секунд = иппон
}

VICTORY_TYPES = {
    'IPPON': 'Иппон',
    'WAZAARI': 'Ваза-ари',
    'WAZAARI_AWASETE_IPPON': 'Два ваза-ари = иппон',
    'YUKO': 'Победа по юко',
    'SHIDO': 'Победа по штрафам',
    'HANSOKU_MAKE': 'Хансоку-маке (дисквалификация)',
    'DECISION': 'Решение судей',
    'FORFEIT': 'Неявка',
    'DISQUALIFICATION': 'Дисквалификация',
    'FUSEN_GACHI': 'Фусэн-гати (неявка)',
    'KIKEN_GACHI': 'Кикэн-гати (отказ)'
}

# Типы штрафов
PENALTY_TYPES = {
    'SHIDO': 'Шидо (легкое нарушение)',
    'HANSOKU_MAKE': 'Хансоку-маке (дисквалификация)'
}

# Максимальное количество штрафов перед дисквалификацией
MAX_PENALTIES = {
    'SHIDO': 3,  # 3 шидо = дисквалификация
    'HANSOKU_MAKE': 1  # 1 хансоку-маке = дисквалификация
}

USER_ROLES = {
    'ADMIN': 'Администратор',
    'REFEREE': 'Судья',
    'SCOREBOARD': 'Табло',
    'VIEWER': 'Зритель',
    'ATHLETE': 'Участник'
}

# Техники для журналирования
TECHNIQUES = {
    'THROW': {
        'SEOI_NAGE': 'Сэой-нагэ',
        'O_UCHI_GARI': 'О-учи-гари',
        'KO_UCHI_GARI': 'Ко-учи-гари',
        'UCHI_MATA': 'Учи-мата',
        'HARAI_GOSHI': 'Харай-госи',
        'SASAE_TSUKIKOMI_ASHI': 'Сасаэ-цукикоми-аси',
        'TAI_OTOSHI': 'Тай-отоси',
        'IPPON_SEOI_NAGE': 'Иппон-сэой-нагэ'
    },
    'OSAEKOMI': {
        'KESA_GATAME': 'Кэса-гатамэ',
        'KAMI_SHIHO_GATAME': 'Ками-сихо-гатамэ',
        'YOKO_SHIHO_GATAME': 'Ёко-сихо-гатамэ',
        'TATE_SHIHO_GATAME': 'Татэ-сихо-гатамэ'
    },
    'SHIME_WAZA': {
        'HADAKA_JIME': 'Хадака-дзимэ',
        'KATA_JUJI_JIME': 'Ката-дзюдзи-дзимэ'
    },
    'KANSETSU_WAZA': {
        'UDE_GARAMI': 'Удэ-гарами',
        'JUJI_GATAME': 'Дзюдзи-гатамэ'
    }
}

# Статусы схватки
FIGHT_STATUSES = {
    'SCHEDULED': 'Запланирована',
    'LIVE': 'В процессе',
    'PAUSED': 'Приостановлена',
    'COMPLETED': 'Завершена',
    'CANCELLED': 'Отменена',
    'REPLAY': 'Переигровка'
}

# Цвета спортсменов
ATHLETE_COLORS = {
    'WHITE': 'Белый',
    'BLUE': 'Синий'
}
