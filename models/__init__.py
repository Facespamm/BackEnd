from models.AthleteTournamentRegistration import AthleteTournamentRegistration

from models.category_new import CategoryNew
from models.fight_new import FightNew
from models.new_associations import (
    AthleteRegistration,
    FightReferee,
    TournamentCategory,
)
from models.new_athlete import AthleteNew
from models.new_club import ClubNew
from models.new_dan import DanNew
from models.new_referee import RefereeNew
from models.new_user import UserNew
from models.result_new import ResultNew
from models.role_new import RoleNew
from models.score_event import ScoreEvent
from models.tatami_fight import TatamiFight
from models.tournament_new import TournamentNew
from models.weighing_new import WeighingNew

__all__ = [
    "AthleteTournamentRegistration",
    "AthleteNew",
    "AthleteRegistration",
    "CategoryNew",
    "ClubNew",
    "DanNew",
    "FightNew",
    "FightReferee",
    "RefereeNew",
    "ResultNew",
    "RoleNew",
    "ScoreEvent",
    "TatamiFight",
    "TournamentNew",
    "TournamentCategory",
    "UserNew",
    "WeighingNew",
]
