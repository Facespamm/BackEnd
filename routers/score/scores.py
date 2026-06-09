from fastapi import APIRouter

from routers.score.schemas import (
    AthleteColorRequest,
    EventsBatchRequest,
    PenaltyRequest,
    ScoreTechniqueRequest,
)
from utils.helpers import error_response

scores_router = APIRouter(prefix="/api/scores", tags=["Scores"])


def _score_manager(fight_id: int):
    from services.score_manager import ScoreManager

    return ScoreManager(fight_id)


@scores_router.post("/fight/{fight_id}/yuko")
def add_yuko(fight_id: int, data: AthleteColorRequest):
    """Добавить оценку ЮКО"""
    try:
        return _score_manager(fight_id).add_yuko(data.athlete_color)
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.post("/fight/{fight_id}/events/batch")
def save_events_batch(fight_id: int, data: EventsBatchRequest):
    """Сохранить события боя пачкой"""
    try:
        return _score_manager(fight_id).save_fight_events(data.events)
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.get("/fight/{fight_id}/timeline")
def get_fight_timeline(fight_id: int):
    """Получить хронологию боя"""
    try:
        return _score_manager(fight_id).get_fight_timeline()
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.get("/fight/{fight_id}/summary")
def get_match_summary(fight_id: int):
    """Получить сводку матча"""
    try:
        return _score_manager(fight_id).get_match_summary()
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.post("/fight/{fight_id}/wazaari")
def add_wazaari(fight_id: int, data: ScoreTechniqueRequest):
    """Добавить оценку ВАЗА-АРИ"""
    try:
        return _score_manager(fight_id).add_wazaari(
            data.athlete_color,
            data.technique,
        )
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.post("/fight/{fight_id}/ippon")
def add_ippon(fight_id: int, data: ScoreTechniqueRequest):
    """Добавить оценку ИППОН"""
    try:
        return _score_manager(fight_id).add_ippon(
            data.athlete_color,
            data.technique,
        )
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.post("/fight/{fight_id}/osaekomi/start")
def start_osaekomi(fight_id: int, data: AthleteColorRequest):
    """Начать отсчет ОСАЕКОМИ"""
    try:
        return _score_manager(fight_id).start_osaekomi(data.athlete_color)
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.post("/fight/{fight_id}/osaekomi/stop")
def stop_osaekomi(fight_id: int):
    """Остановить отсчет ОСАЕКОМИ"""
    try:
        return _score_manager(fight_id).stop_osaekomi()
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.post("/fight/{fight_id}/penalty")
def add_penalty(fight_id: int, data: PenaltyRequest):
    """Добавить штраф"""
    try:
        return _score_manager(fight_id).add_penalty(
            data.athlete_color,
            data.penalty_type,
        )
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.post("/fight/{fight_id}/undo")
def undo_action(fight_id: int):
    """Отменить последнее действие"""
    try:
        return _score_manager(fight_id).undo_last_action()
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.post("/fight/{fight_id}/reset")
def reset_scores(fight_id: int):
    """Сбросить все оценки"""
    try:
        return _score_manager(fight_id).reset_scores()
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.get("/fight/{fight_id}/current")
def get_current_scores(fight_id: int):
    """Получить текущие оценки"""
    try:
        return _score_manager(fight_id).get_current_scores()
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.post("/fight/{fight_id}/rematch")
def rematch_fight(fight_id: int):
    """Переигровка - полный сброс результата боя"""
    try:
        return _score_manager(fight_id).rematch_fight()
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@scores_router.post("/fight/{fight_id}/golden-score")
def enter_golden_score(fight_id: int):
    """Перейти в золотой скор"""
    return error_response(
        "Переход в golden score не реализован для текущей модели боя",
        501,
    )
