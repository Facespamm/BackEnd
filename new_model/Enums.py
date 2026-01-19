from enum import Enum

class Gender(Enum):
    male = 0,
    female = 1

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
    ADMIN ='Администратор',
    REFEREE = 'Судья',
    SCOREBOARD = 'Табло',
    VIEWER = 'Зритель',
    ATHLETE = 'Участник'

def translate_gender(gender):
    return Gender.male if gender == 'мужской' else Gender.female