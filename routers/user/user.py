from fastapi import Depends
from fastapi.routing import APIRouter
from models.Enums import RoleName
from repository.athlete_repo import AthleteRepository
from repository.category_repo import CategoryRepository
from repository.tournament_repo import TournamentRepository
from utils.helpers import error_response
from utils.security import require_role

user_router = APIRouter(prefix="/api/user", tags=["Users"])


@user_router.post("/assign_to_tournament/{tournament_id}")
def assign_to_tournament(
    tournament_id: int, user_id: int = Depends(require_role(RoleName.ATHLETE.value))
):
    with (
        TournamentRepository() as tourn_repository,
        AthleteRepository() as athlete_repository,
    ):
        tournament = tourn_repository.get_tournament_by_id(tournament_id)

        if not tournament:
            return error_response("Нет такого турнира или категории", 404)

        athlete_id = athlete_repository.get_athlete_id_by_user(user_id)
        if athlete_id is None:
            return error_response("Вы не дзюдоист", 400)

        athlete = athlete_repository.get_athlete_by_id(athlete_id)
        if not athlete:
            return error_response("Вы не дзюдоист", 400)

        if tourn_repository.is_registet_on_tournament(tournament_id, athlete_id):
            return {
                "success": True,
                "message": "Вы зврегестрированы на этот турнир зарание",
            }

        categories = tourn_repository.get_categories(tournament_id)
        if not categories:
            return error_response("Нет категорий за турнир", 404)

        unsuitable_catigory_count = 0
        for category in categories:
            age_ok = category.min_year <= athlete.birth_date.year <= category.max_year
            gender_ok = category.gender.name == athlete.gender
            if not (age_ok and gender_ok):
                continue
            else:
                unsuitable_catigory_count += 1

        if unsuitable_catigory_count == len(categories):
            return error_response(
                "Нет подходящей категории в которой вы могли участвовать", 404
            )

        try:
            has_assigned_athlete = tourn_repository.assign_athletes_tournament(
                tournament_id, athlete_id, user_id
            )
        except Exception as e:
            return error_response(f"Ошибка регистрации на турнир:{e}", 500)

        tournament_name = tournament.name
    if has_assigned_athlete:
        return {
            "success": True,
            "message": f"Вы зарегестрированы на турнир {tournament_name}",
        }


@user_router.patch("/unassign_to_tournament/{tournament_id}")
def unassign_to_tournament(
    tournament_id: int, user_id: int = Depends(require_role(RoleName.ATHLETE.value))
):
    with (
        TournamentRepository() as tourn_repository,
        AthleteRepository() as athlete_repository,
    ):
        tournament = tourn_repository.get_tournament_by_id(tournament_id)

        if not tournament:
            return error_response("Нет такого турнира или категории", 404)

        athlete_id = athlete_repository.get_athlete_id_by_user(user_id)
        if athlete_id is None:
            return error_response("Вы не дзюдоист", 404)

        try:
            has_unassign = tourn_repository.unassign_athlete_to_tournament(
                tournament_id, athlete_id
            )
        except Exception as e:
            return error_response(f"Ошибка отмены регистрации:{e}", 500)

    if has_unassign:
        return {"success": True, "message": "Вы отменили регистрацию"}


@user_router.get("/is_registered/{tournament_id}")
def is_registered(
    tournament_id: int, user_id: int = Depends(require_role(RoleName.ATHLETE.value))
):
    with (
        TournamentRepository() as tourn_repository,
        AthleteRepository() as athlete_repository,
    ):
        athlete_id = athlete_repository.get_athlete_id_by_user(user_id)
        is_registered = tourn_repository.is_registet_on_tournament(
            tournament_id, athlete_id
        )
    return {"is_registered": is_registered}
