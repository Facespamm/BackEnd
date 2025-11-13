"""
Константы правил дзюдо и системные настройки
"""

# Система рангов дзюдо
JUDO_RANKS = {
    '6KYU': '6 кю (белый)',
    '5KYU': '5 кю (желтый)',
    '4KYU': '4 кю (оранжевый)',
    '3KYU': '3 кю (зеленый)',
    '2KYU': '2 кю (синий)',
    '1KYU': '1 кю (коричневый)',
    '1DAN': '1 дан (черный)',
    '2DAN': '2 дан (черный)',
    '3DAN': '3 дан (черный)',
    '4DAN': '4 дан (черный)',
    '5DAN': '5 дан (черный)',
    '6DAN': '6 дан (красно-белый)',
    '7DAN': '7 дан (красно-белый)',
    '8DAN': '8 дан (красно-белый)',
    '9DAN': '9 дан (красный)',
    '10DAN': '10 дан (красный)'
}

# Типы штрафов (Shido)
PENALTY_TYPES = {
    'SHIDO': 'Шидо (легкое нарушение)',
    'HANSOKU_MAKE': 'Хансоку-маке (дисквалификация)'
}

# Технические действия (Waza)
TECHNIQUES = {
    'NAGE_WAZA': {
        'TE_WAZA': ['Seoi-nage', 'Tai-otoshi', 'Kata-guruma', 'Sukui-nage', 'Uki-otoshi'],
        'KOSHI_WAZA': ['O-goshi', 'Ushiro-goshi', 'Koshi-guruma', 'Tsuri-komi-goshi'],
        'ASHI_WAZA': ['O-soto-gari', 'O-uchi-gari', 'Ko-soto-gari', 'Ko-uchi-gari', 'De-ashi-barai'],
        'MA_SUTEMI_WAZA': ['Tomoe-nage', 'Sumi-gaeshi', 'Hikikomi-gaeshi'],
        'YOKO_SUTEMI_WAZA': ['Yoko-gake', 'Yoko-guruma', 'Uki-waza']
    },
    'KATAME_WAZA': {
        'OSAE_KOMI_WAZA': ['Kesa-gatame', 'Kata-gatame', 'Kami-shiho-gatame', 'Yoko-shiho-gatame'],
        'SHIME_WAZA': ['Nami-juji-jime', 'Gyaku-juji-jime', 'Hadaka-jime', 'Okuri-eri-jime'],
        'KANSETSU_WAZA': ['Ude-garami', 'Ude-hishigi-juji-gatame', 'Ude-hishigi-ude-gatame']
    }
}

# Очки за разные типы побед
VICTORY_POINTS = {
    'IPPON': 100,
    'WAZAARI_AWASETE_IPPON': 90,
    'WAZAARI': 10,
    'YUKO': 1,
    'SHIDO': 0
}

# Статусы турнира
TOURNAMENT_STATUS = {
    'PLANNED': 'Запланирован',
    'REGISTRATION': 'Регистрация',
    'WEIGHING': 'Взвешивание',
    'BRACKETS': 'Формирование сеток',
    'LIVE': 'В процессе',
    'COMPLETED': 'Завершен',
    'CANCELLED': 'Отменен'
}

# Статусы схватки
FIGHT_STATUS = {
    'SCHEDULED': 'Запланирована',
    'LIVE': 'В процессе',
    'COMPLETED': 'Завершена',
    'CANCELLED': 'Отменена'
}

# Типы сеток
BRACKET_TYPES = {
    'SINGLE_ELIMINATION': 'Олимпийская система',
    'DOUBLE_ELIMINATION': 'Система с утешительными',
    'ROUND_ROBIN': 'Круговая система'
}

# Уровни судей
REFEREE_LEVELS = {
    'NATIONAL_3': 'Национальный 3 категории',
    'NATIONAL_2': 'Национальный 2 категории',
    'NATIONAL_1': 'Национальный 1 категории',
    'CONTINENTAL_C': 'Континентальный C',
    'CONTINENTAL_B': 'Континентальный B',
    'CONTINENTAL_A': 'Континентальный A',
    'INTERNATIONAL_C': 'Международный C',
    'INTERNATIONAL_B': 'Международный B',
    'INTERNATIONAL_A': 'Международный A'
}

# Страны для выбора
COUNTRIES = [
    'Россия', 'Беларусь', 'Казахстан', 'Узбекистан', 'Азербайджан',
    'Армения', 'Грузия', 'Украина', 'Молдова', 'Кыргызстан',
    'Таджикистан', 'Туркменистан', 'Литва', 'Латвия', 'Эстония'
]

# Города России
RUSSIAN_CITIES = [
    'Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань',
    'Нижний Новгород', 'Челябинск', 'Самара', 'Омск', 'Ростов-на-Дону',
    'Уфа', 'Красноярск', 'Воронеж', 'Пермь', 'Волгоград'
]

# Временные зоны
TIMEZONES = [
    'UTC+2', 'UTC+3', 'UTC+4', 'UTC+5', 'UTC+6', 'UTC+7', 'UTC+8', 'UTC+9', 'UTC+10'
]

# Форматы экспорта
EXPORT_FORMATS = {
    'PDF': 'PDF документ',
    'EXCEL': 'Excel таблица',
    'JSON': 'JSON данные',
    'CSV': 'CSV файл'
}