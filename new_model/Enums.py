from enum import Enum

class Gender(Enum):
    male = 'мужской'
    female = 'женский'

class EventType(Enum):
    SCORE = 'SCORE'
    PENALTY = 'PENALTY'
    OSAEKOMI_START = 'OSAEKOMI_START'
    OSAEKOMI_STOP = 'OSAEKOMI_STOP'

class AthleteColor(Enum):
    WHITE = 'WHITE'
    BLUE = 'BLUE'

class ScoreType(Enum):
    YUKO = 'YUKO'
    WAZAARI = 'WAZAARI'
    IPPON = 'IPPON'
    SHIDO = 'SHIDO'

class VictoryType(Enum):
    IPPON = 'Ипон'
    WAZAARI = 'Ваза-ари'
    WAZAARI_AWASETE_IPPON = 'Два ваза-ари = иппон'
    YUKO = 'Победа по юко'
    SHIDO = 'Победа по штрафам'
    HANSOKU_MAKE = 'Хансоку-маке (дисквалификация)'
    DECISION = 'Решение судей'
    FORFEIT = 'Неявка'
    DISQUALIFICATION = 'Дисквалификация'
    FUSEN_GACHI = 'Фусэн-гати (неявка)'
    KIKEN_GACHI = 'Кикэн-гати (отказ)'

class StatusTournament(Enum):
    PLANNED = 'PLANNED'
    REGISTRATION = 'REGISTRATION'
    WEIGHING = 'WEIGHING'
    BRACKETS = 'BRACKETS'
    LIVE = 'LIVE'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'

class FightStatus(Enum):
    SCHEDULED = 'SCHEDULED'
    LIVE = 'LIVE'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'
    REPLAY = 'REPLAY'

class RoleName(Enum):
    ADMIN ='Администратор'
    REFEREE = 'Судья'
    SCOREBOARD = 'Табло'
    VIEWER = 'Зритель'
    ATHLETE = 'Участник'

class RefereeLevels(Enum):
    NATIONAL_3 = 'Национальный 3 категории'
    NATIONAL_2 = 'Национальный 2 категории'
    NATIONAL_1 = 'Национальный 1 категории'
    CONTINENTAL_C = 'Континентальный C'
    CONTINENTAL_B = 'Континентальный B'
    CONTINENTAL_A = 'Континентальный A'
    INTERNATIONAL_C = 'Международный C'
    INTERNATIONAL_B = 'Международный B'
    INTERNATIONAL_A = 'Международный A'

class BracketType(Enum):
    MAIN = 'MAIN'
    SEMIFINALIST_CONSOLATION_GROUP_A = 'SEMIFINALIST_CONSOLATION_GROUP_A'
    SEMIFINALIST_CONSOLATION_GROUP_B = 'SEMIFINALIST_CONSOLATION_GROUP_B'
    FINALIST_CONSOLATION_GROUP_A = 'FINALIST_CONSOLATION_GROUP_A'
    FINALIST_CONSOLATION_GROUP_B = 'FINALIST_CONSOLATION_GROUP_B'

class ConsolationType(Enum):
    SEMIFINALISTS = 'SEMIFINALISTS'
    FINALISTS = 'FINALISTS'

class TatamiStatus(Enum):
    FREE = 'Свободно'
    TAKEN = 'Занята'

def translate_gender(gender):
    return Gender.male.name if gender == 'мужской' else Gender.female.name

def text_to_referee_level(text: str):
    normolize_name = text.strip().lower()

    for level in RefereeLevels:
        if normolize_name == level.value.strip().lower():
            return level

    return  None

def text_to_fight_status(text: str):
    normolize_name = text.strip().lower()

    for status in FightStatus:
        if normolize_name == status.value.strip().lower():
            return status

    return None