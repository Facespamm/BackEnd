from fastapi import APIRouter, Query

from database.db import create_session
from models.Enums import FightStatus
from repository.athlete_repo import AthleteRepository
from repository.figth_repo import FightRepository
from repository.result_repo import ResultRepository
from routers.result.schemas import ResultDTO
from utils.helpers import error_response

results_router = APIRouter(prefix="/api/results", tags=["Results"])


# TODO Переписать вот это
@results_router.get("/")
def get_results(
    tournament_id: int = Query(gt=0),
    category_id: int = Query(gt=0),
):
    """Получить список результатов"""
    try:
        with create_session() as session:
            result_repo = ResultRepository(session)
            results = result_repo.get_results_by_tournament(tournament_id, category_id)

            athlete_repo = AthleteRepository(session)
            result_data = [
                ResultDTO.from_result(
                    result,
                    winner_name=athlete_repo.get_athlete_name_data(result.winner_id),
                ).model_dump()
                for result in results
            ]

        return {"success": True, "results": result_data, "total": len(result_data)}

    except Exception as e:
        return error_response(f"Ошибка при получении результатов: {str(e)}", 500)


@results_router.get("/{result_id}")
def get_result(result_id: int):
    """Получить конкретный результат"""
    try:
        with create_session() as session:
            result_repo = ResultRepository(session)
            result = result_repo.get_result_by_id(result_id)

            if not result:
                return error_response("Результат не найден", 404)

            athlete_repo = AthleteRepository(session)
            result_data = ResultDTO.from_result(
                result,
                winner_name=athlete_repo.get_athlete_name_data(result.winner_id),
            ).model_dump()

        return result_data

    except Exception as e:
        return error_response(f"Ошибка при получении результата: {str(e)}", 500)


@results_router.patch("/{fight_id}/cancel-result")
def cancel_result(fight_id: int):
    """Отменить результат боя"""
    try:
        with create_session() as session:
            fight_repo = FightRepository(session)
            fight = fight_repo.get_fight_by_id(fight_id)

            if not fight:
                return error_response("Бой не найден", 404)

            result_repo = ResultRepository(session)
            result = result_repo.get_result_by_fight(fight_id)

            if not result:
                return error_response("Не найден результат по бою", 404)

            fight.status = FightStatus.CANCELLED
            winner_id = result.winner_id
            is_deleted_result = result_repo.delete_result(fight_id)

            if not is_deleted_result:
                return error_response("Не получилось удалить результат боя", 500)

            fight_repo.remove_winner_from_next_fight(fight_id, winner_id)

        return {"success": True, "message": "Отменены результаты боя"}

    except Exception as e:
        return error_response(f"Ошибка {str(e)}", 500)
