from fastapi import APIRouter

from database.db import create_session
from repository.athlete_repo import AthleteRepository
from repository.category_repo import CategoryRepository
from repository.figth_repo import FightRepository
from repository.result_repo import ResultRepository
from repository.tournament_repo import TournamentRepository
from routers.bracket.schemas import BaseResponse, FightsResponse
from services.bracket_generator import BracketGenerator
from utils.helpers import calculate_rounds, error_response
from utils.security import admin_depd

brackets_router = APIRouter(prefix="/api/brackets", tags=["Brackets"])


@brackets_router.get(
    "/{tournament_id}/first_fights",
    response_model=FightsResponse,
    dependencies=[admin_depd],
)
async def first_fights(tournament_id: int, category_id: int):
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(
                tournament_id, category_id
            )
            if not tournament_category:
                return error_response("Категория турнира не найдена", 404)

            tournament_category_id = tournament_category.tournament_category_id

            fight_repo = FightRepository(session)
            fights = fight_repo.get_fight_by_tournament(
                tournament_category_id, minimal_round_number=1
            )  # самый первый раунд это первый

            athlete_repo = AthleteRepository(session)
            fights_dtos = [
                {
                    "id": fight.id,
                    "blue_athlete": athlete_repo.get_athlete_by_fight(
                        fight.blue_athlete_id, fight.id
                    )
                    if fight.blue_athlete_id
                    else None,
                    "white_athlete": athlete_repo.get_athlete_by_fight(
                        fight.white_athlete_id, fight.id
                    )
                    if fight.white_athlete_id
                    else None,
                    "tatami_number": fight.tatami_number,
                    "round": fight.round_number,
                    "status_fight": fight.status.value,
                    "next_fight": fight.next_fight_id,
                    "type_bracket": fight.type_bracket.value,
                }
                for fight in fights
            ]

            tournament_name = (
                tournament_repo.get_tournament_name_by_tournament_category(
                    tournament_category_id
                )
            )

            category_repo = CategoryRepository(session)
            category = category_repo.get_category_by_id(category_id)
            # ✅ Извлекаем все данные из объекта ВНУТРИ сессии
            category_dto = (
                {
                    "id": category.id,
                    "name": category.name,
                    "weight_range": f"от {category.min_weight} до {category.max_weight}",
                }
                if category
                else None
            )

            winner = None
            if fights:
                last_fight = fights[-1]
                result_repo = ResultRepository(session)
                has_result = result_repo.get_result_by_fight(last_fight.id)
                if has_result:
                    winner = athlete_repo.get_athlete_by_fight(
                        has_result.winner_id, last_fight.id
                    )

        if not fights_dtos:
            return error_response("Нет боев", 404)

        return {
            "success": True,
            "fights": fights_dtos,
            "tournament_name": tournament_name,
            "category": category_dto,
            "winner": winner,
        }
    except Exception as e:
        return error_response(f"Ошибка вывода боев: {str(e)}", 500)


@brackets_router.get(
    "/{tournament_id}/fights", response_model=FightsResponse, dependencies=[admin_depd]
)
async def fight_bracket(tournament_id: int, category_id: int):
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(
                tournament_id, category_id
            )
            if not tournament_category:
                return error_response("Категория турнира не найдена", 404)

            tournament_category_id = tournament_category.tournament_category_id

            fight_repo = FightRepository(session)
            fights = fight_repo.get_fight_by_tournament(tournament_category_id)

            athlete_repo = AthleteRepository(session)
            fights_dtos = [
                {
                    "id": fight.id,
                    "blue_athlete": athlete_repo.get_athlete_by_fight(
                        fight.blue_athlete_id, fight.id
                    )
                    if fight.blue_athlete_id
                    else None,
                    "white_athlete": athlete_repo.get_athlete_by_fight(
                        fight.white_athlete_id, fight.id
                    )
                    if fight.white_athlete_id
                    else None,
                    "tatami_number": fight.tatami_number,
                    "round": fight.round_number,
                    "status_fight": fight.status.value,
                    "next_fight": fight.next_fight_id,
                    "type_bracket": fight.type_bracket.value,
                }
                for fight in fights
            ]

            tournament_name = (
                tournament_repo.get_tournament_name_by_tournament_category(
                    tournament_category_id
                )
            )

            category_repo = CategoryRepository(session)
            category = category_repo.get_category_by_id(category_id)
            # ✅ Извлекаем все данные из объекта ВНУТРИ сессии
            category_dto = (
                {
                    "id": category.id,
                    "name": category.name,
                    "weight_range": f"от {category.min_weight} до {category.max_weight}",
                }
                if category
                else None
            )

            winner = None
            if fights:
                last_fight = fights[-1]
                result_repo = ResultRepository(session)
                has_result = result_repo.get_result_by_fight(last_fight.id)
                if has_result:
                    winner = athlete_repo.get_athlete_by_fight(
                        has_result.winner_id, last_fight.id
                    )

        if not fights_dtos:
            return error_response("Нет боев", 404)

        return {
            "success": True,
            "fights": fights_dtos,
            "tournament_name": tournament_name,
            "category": category_dto,
            "winner": winner,
        }
    except Exception as e:
        return error_response(f"Ошибка вывода боев: {str(e)}", 500)


@brackets_router.get(
    "/{tournament_id}/has-olympic-consolation",
    response_model=BaseResponse,
    dependencies=[admin_depd],
)
async def has_consolation_fights(tournament_id: int, category_id: int):
    """Проверяет можно ли создать утешительные бои"""
    with create_session() as session:
        tournament_repo = TournamentRepository(session)
        tournament_category = tournament_repo.get_tournament_category(
            tournament_id, category_id
        )

        if not tournament_category:
            return error_response("Категория турнира не найдена", 404)

        if not tournament_category.has_consolidation_fights:
            return error_response("Утешительные бои не включены", 400)

        athlete_repo = AthleteRepository(session)
        athletes = athlete_repo.get_athletes_by_tournament(tournament_id, category_id)

        total_rounds = calculate_rounds(len(athletes))

        fight_repo = FightRepository(session)
        semi_final_fights = fight_repo.get_semi_final_fights(
            tournament_category.tournament_category_id, total_rounds - 1
        )

    semi_final_fights_not_none = [
        f
        for f in semi_final_fights
        if f.blue_athlete_id is not None and f.white_athlete_id is not None
    ]

    if len(semi_final_fights_not_none) < 2:
        return error_response("Недостаточно полуфинальных боев", 400)

    return {"success": True}


@brackets_router.post(
    "/{tournament_id}/olympic", response_model=BaseResponse, dependencies=[admin_depd]
)
async def create_bracket(tournament_id: int, category_id: int, tatami_number: int):
    """Создает олимпийскую сетку"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)
            if not tournament:
                return error_response("Турнир не найден", 404)

            category = tournament_repo.get_category(tournament_id, category_id)
            if not category:
                return error_response("Категория не найдена в этом турнире", 404)

        bracket_generator = BracketGenerator(tournament_id)
        generate_fights = bracket_generator.generate_olympic(category_id, tatami_number)

        if not generate_fights:
            return error_response(
                "Не удалось создать бои (возможно, недостаточно спортсменов в категории)",
                400,
            )

        return {"success": True, "message": "Сетка успешно создана"}

    except Exception as e:
        return error_response(f"Ошибка создания сетки: {str(e)}", 500)


@brackets_router.post(
    "/{tournament_id}/olympic/semifinals-consolation",
    response_model=BaseResponse,
    dependencies=[admin_depd],
)
async def generate_semifinals_consolation_fights(
    tournament_id: int, category_id: int, tatami_number: int
):
    """Создание утешительных боев от полуфиналистов"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(
                tournament_id, category_id
            )
            if not tournament_category:
                return error_response("Категория турнира не найдена", 404)

        bracket_generator = BracketGenerator(tournament_id)
        generated_fights = (
            bracket_generator.generate_olympic_consolation_fight_semifinal(
                category_id, tatami_number
            )
        )

        if not generated_fights:
            return error_response("Утешительные бои не созданы", 400)

        return {"success": True, "message": "Утешительные бои успешно созданы"}
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@brackets_router.post(
    "/{tournament_id}/olympic/finals-consolation",
    response_model=BaseResponse,
    dependencies=[admin_depd],
)
async def generate_consolation_fights_finalist(
    tournament_id: int, category_id: int, tatami_number: int
):
    """Создание сетки для утешительных от финалистов"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(
                tournament_id, category_id
            )
            if not tournament_category:
                return error_response("Категория турнира не найдена", 404)

        bracket_generator = BracketGenerator(tournament_id)
        generated_fights = bracket_generator.generate_olympic_consolation_fight_final(
            category_id, tatami_number
        )

        if not generated_fights:
            return error_response("Утешительные бои не созданы", 400)

        return {"success": True, "message": "Утешительные бои успешно созданы"}
    except Exception as e:
        return error_response(
            f"Ошибка создания утешительных боев: {str(e)}",
            500,
        )
