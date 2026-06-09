from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from database.db import create_session
from models.Enums import BracketType, FightStatus
from repository.athlete_repo import AthleteRepository
from repository.category_repo import CategoryRepository
from repository.figth_repo import FightRepository
from repository.referee_repo import RefereeRepository
from repository.result_repo import ResultRepository
from repository.tournament_repo import TournamentRepository
from routers.fight.schemas import (
    AssignRefereeRequest,
    ChangeAthletesRequest,
    EndFightRequest,
    FightDTO,
    FilterQueryParam,
)
from utils.helpers import error_response

fights_router = APIRouter(prefix="/api/fights", tags=["Fights"])


def _build_result_dto(result):
    if not result:
        return None
    return {
        "winner_id": result.winner_id,
        "victory_type": result.victory_type.value if result.victory_type else None,
        "fight_duration": result.fight_duration,
    }


def _get_athlete_dto(athlete_repo: AthleteRepository, athlete_id, fight_id: int):
    if not athlete_id:
        return None
    return athlete_repo.get_athlete_by_fight(athlete_id, fight_id)


def _build_fight_dto(fight, athlete_repo, result_repo=None):
    result = result_repo.get_result_by_fight(fight.id) if result_repo else None
    return {
        "id": fight.id,
        "round": fight.round_number,
        "fight_number": fight.fight_number,
        "status": fight.status.value
        if hasattr(fight.status, "value")
        else fight.status,
        "tatami_number": fight.tatami_number,
        "next_fight": fight.next_fight_id,
        "white_athlete": _get_athlete_dto(
            athlete_repo, fight.white_athlete_id, fight.id
        ),
        "blue_athlete": _get_athlete_dto(athlete_repo, fight.blue_athlete_id, fight.id),
        "result": _build_result_dto(result),
    }


@fights_router.get("/")
def get_fights(params: Annotated[FilterQueryParam, Depends()]):
    """Получить список схваток"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(params.tournament_id)
            if not tournament:
                return error_response("Турнир не найден", status_code=404)

            fight_repo = FightRepository(session)
            fights = fight_repo.get_fights_by_search_params(
                params.tournament_id,
                params.tatami,
                params.status,
            )

            athlete_repo = AthleteRepository(session)
            result = [
                FightDTO.from_fight(
                    fight,
                    white_athlete=_get_athlete_dto(
                        athlete_repo, fight.white_athlete_id, fight.id
                    ),
                    blue_athlete=_get_athlete_dto(
                        athlete_repo, fight.blue_athlete_id, fight.id
                    ),
                ).model_dump()
                for fight in fights
            ]

        return {"success": True, "fights": result, "total": len(result)}

    except Exception as e:
        return error_response(f"Ошибка при получении схваток: {str(e)}", 500)


@fights_router.get("/{fight_id}")
def get_fight(fight_id: int):
    """Получить информацию о схватке"""
    try:
        with create_session() as session:
            fight_repo = FightRepository(session)
            fight = fight_repo.get_fight_by_id(fight_id)
            if not fight:
                return error_response("Схватка не найдена", 404)

            athlete_repo = AthleteRepository(session)
            fight_data = FightDTO.from_fight(
                fight,
                white_athlete=_get_athlete_dto(
                    athlete_repo, fight.white_athlete_id, fight.id
                ),
                blue_athlete=_get_athlete_dto(
                    athlete_repo, fight.blue_athlete_id, fight.id
                ),
            ).model_dump()

        return fight_data

    except Exception as e:
        return error_response(f"Ошибка при получении схватки: {str(e)}", 500)


@fights_router.get("/{tournament_id}/consolation/finalists")
def get_finalists_consolation(
    tournament_id: int,
    category: int = Query(gt=0),
    group: Optional[str] = Query(default=None),
):
    """Утешительные бои финалистов (группа A и B)"""
    try:
        group = group.upper() if group else None

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(
                tournament_id, category
            )
            if not tournament_category:
                return error_response("Категория турнира не найдена", 404)

            fight_repo = FightRepository(session)
            athlete_repo = AthleteRepository(session)
            result_repo = ResultRepository(session)

            groups = {
                "A": BracketType.FINALIST_CONSOLATION_GROUP_A,
                "B": BracketType.FINALIST_CONSOLATION_GROUP_B,
            }
            groups_to_fetch = {group: groups[group]} if group in groups else groups

            result = {}
            for group_name, bracket_type in groups_to_fetch.items():
                fights = fight_repo.get_fights_by_bracket_type(
                    tournament_category.tournament_category_id,
                    bracket_type,
                )
                result[f"group_{group_name}"] = [
                    _build_fight_dto(fight, athlete_repo, result_repo)
                    for fight in fights
                ]

            if not any(result.values()):
                return error_response("Утешительные бои финалистов не найдены", 404)

        return {
            "success": True,
            **result,
            "total": sum(len(v) for v in result.values()),
        }

    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@fights_router.get("/{tournament_id}/consolation/semifinalists")
def get_semifinalists_consolation(
    tournament_id: int,
    category: int = Query(gt=0),
):
    """Утешительные бои полуфиналистов - обе группы A и B одним запросом"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(
                tournament_id, category
            )
            if not tournament_category:
                return error_response("Категория турнира не найдена", 404)

            tournament_category_id = tournament_category.tournament_category_id
            fight_repo = FightRepository(session)
            athlete_repo = AthleteRepository(session)
            result_repo = ResultRepository(session)

            fights_a = fight_repo.get_fights_by_bracket_type(
                tournament_category_id,
                BracketType.SEMIFINALIST_CONSOLATION_GROUP_A,
            )
            fights_b = fight_repo.get_fights_by_bracket_type(
                tournament_category_id,
                BracketType.SEMIFINALIST_CONSOLATION_GROUP_B,
            )

            fights_dtos_a = [
                _build_fight_dto(fight, athlete_repo, result_repo) for fight in fights_a
            ]
            fights_dtos_b = [
                _build_fight_dto(fight, athlete_repo, result_repo) for fight in fights_b
            ]

        return {
            "success": True,
            "groups": {
                "A": {"fights": fights_dtos_a, "total": len(fights_dtos_a)},
                "B": {"fights": fights_dtos_b, "total": len(fights_dtos_b)},
            },
            "total": len(fights_dtos_a) + len(fights_dtos_b),
        }

    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@fights_router.get("/{fight_id}/referees")
def get_fight_referees(fight_id: int):
    """Получить судей, назначенных на схватку"""
    try:
        with create_session() as session:
            fight_repo = FightRepository(session)
            fight = fight_repo.get_fight_by_id(fight_id)
            if not fight:
                return error_response("Схватка не найдена", 404)

            referee_list = fight_repo.get_fight_referees(fight_id)

        return {"success": True, "referees": referee_list}

    except Exception as e:
        return error_response(f"Ошибка при получении судей схватки: {str(e)}", 500)


@fights_router.post("/{fight_id}/assign_referee")
def assign_referee_to_fight(fight_id: int, data: AssignRefereeRequest):
    """Назначить судью на схватку"""
    try:
        with create_session() as session:
            fight_repo = FightRepository(session)
            fight = fight_repo.get_fight_by_id(fight_id)
            if not fight:
                return error_response("Схватка не найдена", 404)

            referee_repo = RefereeRepository(session)
            referee = referee_repo.get_referee(data.referee_id)
            if not referee:
                return error_response("Судья не найден", 404)

            fight_repo.assign_referee(data.referee_id, fight.id, data.role)

        return {"success": True, "message": "Судья успешно назначен на схватку"}

    except Exception as e:
        return error_response(f"Ошибка при назначении судьи на схватку: {str(e)}", 500)


@fights_router.delete("/{fight_id}/remove_referee")
def remove_referee_from_fight(fight_id: int, role: str = Query(min_length=1)):
    """Удалить судью со схватки"""
    try:
        with create_session() as session:
            fight_repo = FightRepository(session)
            fight = fight_repo.get_fight_by_id(fight_id)
            if not fight:
                return error_response("Схватка не найдена", 404)

            referee_repo = RefereeRepository(session)
            if not referee_repo.has_assign_referee(role, fight.id):
                return error_response(f"Судья на роль {role} не назначен", 404)

            fight_repo.remove_referee(fight.id, role)

        return {"success": True, "message": "Судья успешно удален с схватки"}

    except Exception as e:
        return error_response(f"Ошибка при удалении судьи с схватки: {str(e)}", 500)


@fights_router.patch("/{fight_id}/set-live")
def update_fight_status(
    fight_id: int,
    tatami_number: int = Query(gt=0),
):
    """Перевести схватку в LIVE"""
    try:
        with create_session() as session:
            fight_repo = FightRepository(session)
            existing_fight = fight_repo.get_fight_by_id(fight_id)
            if not existing_fight:
                return error_response("Схватка не найдена", 404)

            if fight_repo.tatami_is_taken(fight_id, tatami_number):
                return error_response("На татами уже идет бой", 400)

            fight_repo.set_live_status(fight_id, tatami_number)

        return {"success": True}

    except Exception as e:
        return error_response(f"Ошибка при обновлении статуса схватки: {str(e)}", 500)


@fights_router.put("/{fight_id}/end-fight")
def end_fight(fight_id: int, data: EndFightRequest):
    """Завершить схватку"""
    try:
        with create_session() as session:
            fight_repo = FightRepository(session)
            existing_fight = fight_repo.get_fight_by_id(fight_id)
            if not existing_fight:
                return error_response("Схватка не найдена", 404)

            fight_repo.end_fight(fight_id, data.model_dump())

        return {"success": True, "message": "Схватка успешно завершена"}

    except Exception as e:
        return error_response(f"Ошибка при завершении схватки: {str(e)}", 500)


@fights_router.get("/{tournament_id}/scheduled/")
def fight_bracket(
    tournament_id: int,
    category: int = Query(gt=0),
):
    """Получить запланированные схватки по турниру и категории"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(
                tournament_id,
                category,
            )
            if not tournament_category:
                return error_response("Категория турнира не найдена", 404)

            tournament_category_id = tournament_category.tournament_category_id
            fight_repo = FightRepository(session)
            fights = fight_repo.get_fight_by_tournament(
                tournament_category_id,
                FightStatus.SCHEDULED,
            )

            athlete_repo = AthleteRepository(session)
            fights_dtos = [
                {
                    "id": fight.id,
                    "blue_athlete": _get_athlete_dto(
                        athlete_repo, fight.blue_athlete_id, fight.id
                    ),
                    "white_athlete": _get_athlete_dto(
                        athlete_repo, fight.white_athlete_id, fight.id
                    ),
                    "tatami_number": fight.tatami_number,
                    "round": fight.round_number,
                    "status_fight": fight.status.value
                    if hasattr(fight.status, "value")
                    else fight.status,
                    "next_fight": fight.next_fight_id,
                }
                for fight in fights
            ]

            tournament_name = (
                tournament_repo.get_tournament_name_by_tournament_category(
                    tournament_category_id
                )
            )
            category_repo = CategoryRepository(session)
            category_model = category_repo.get_category_by_id(category)

        if not fights_dtos:
            return error_response("Нет боев", 404)

        return {
            "success": True,
            "fights": fights_dtos,
            "tournament_name": tournament_name,
            "category": {
                "id": category_model.id if category_model else None,
                "name": category_model.name if category_model else None,
                "weight_range": (
                    f"от {category_model.min_weight} до {category_model.max_weight}"
                ),
            },
        }

    except Exception as e:
        return error_response(f"Ошибка вывода боев: {str(e)}", 500)


@fights_router.put("/change_athletes/")
def change_athletes(data: ChangeAthletesRequest):
    """Поменять спортсменов между схватками"""
    try:
        with create_session() as session:
            athlete_repo = AthleteRepository(session)
            fights_repo = FightRepository(session)

            first_fight = fights_repo.get_fight_by_id(data.first_fight_id)
            second_fight = fights_repo.get_fight_by_id(data.second_fight_id)

            if not first_fight or not second_fight:
                return error_response("Одна или обе схватки не найдены", 404)

            first_has_both = (
                first_fight.blue_athlete_id and first_fight.white_athlete_id
            )
            second_has_both = (
                second_fight.blue_athlete_id and second_fight.white_athlete_id
            )
            if not first_has_both or not second_has_both:
                return error_response(
                    "Нельзя менять атлетов в бою где есть Пустой боец",
                    400,
                )

            first_athlete = athlete_repo.get_athlete_by_id(data.first_athlete_id)
            second_athlete = athlete_repo.get_athlete_by_id(data.second_athlete_id)
            if not first_athlete or not second_athlete:
                return error_response("Один или оба атлета не найдены", 404)

            if first_fight.blue_athlete_id == data.first_athlete_id:
                first_fight.blue_athlete_id = data.second_athlete_id
            else:
                first_fight.white_athlete_id = data.second_athlete_id

            if second_fight.blue_athlete_id == data.second_athlete_id:
                second_fight.blue_athlete_id = data.first_athlete_id
            else:
                second_fight.white_athlete_id = data.first_athlete_id

            fights_repo.update_athlete_in_next_rounds(
                first_fight,
                data.first_athlete_id,
                data.second_athlete_id,
            )
            fights_repo.update_athlete_in_next_rounds(
                second_fight,
                data.second_athlete_id,
                data.first_athlete_id,
            )
            session.commit()

        return {"success": True, "message": "Спортсмены успешно изменены в схватках"}

    except Exception as e:
        return error_response(
            f"Ошибка при изменении спортсменов в схватке: {str(e)}",
            500,
        )


@fights_router.patch("/{fight_id}/change_tatami")
def change_tatami(
    fight_id: int,
    tatami_number: int = Query(gt=0),
):
    """Изменить татами схватки"""
    try:
        with create_session() as session:
            fights_repo = FightRepository(session)
            fight = fights_repo.get_fight_by_id(fight_id)
            if not fight:
                return error_response("Нет такого боя", 404)

            fights_repo.change_tamami(fight.id, tatami_number)

        return {"success": True, "message": "Татами успешно изменен"}

    except Exception as e:
        return error_response(f"Ошибка при смене татами: {str(e)}", 500)
