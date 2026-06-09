"""
pdf_routes.py
Blueprint для генерации PDF результатов турнира.

Подключить в app.py:
    from pdf_routes import pdf_bp
    app.register_blueprint(pdf_bp)

Endpoint:
    GET /api/pdf/tournament/<tournament_id>

Query params:
    category_id (int, optional) — PDF только для одной категории.
                                   Если не указан — генерирует по всем категориям.

Примеры:
    GET /api/pdf/tournament/5                  → все категории
    GET /api/pdf/tournament/5?category_id=12   → только категория 12
"""

import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from database.db import create_session
from models.Enums import BracketType
from repository.athlete_repo import AthleteRepository
from repository.category_repo import CategoryRepository
from repository.figth_repo import FightRepository
from repository.result_repo import ResultRepository
from repository.tournament_repo import TournamentRepository
from services.pdf_generator import generate_tournament_pdf
from utils.helpers import error_response

pdf_router = APIRouter(prefix="/api/pdf", tags=["Pdf"])


# ─────────────────────────────────────────────────────────────
# Хелпер: собрать пьедестал категории из результатов
# ─────────────────────────────────────────────────────────────


def _get_ath(athlete_id, athlete_repo):
    if not athlete_id:
        return {}
    data = athlete_repo.get_athlete_name_data(athlete_id)
    if data:
        data["id"] = athlete_id
    return data or {}


def _get_club(athlete_id, athlete_repo):
    try:
        ath = athlete_repo.get_athlete_by_id(athlete_id)
        return ath.club.name if ath and ath.club else "—"
    except Exception:
        return "—"


def _build_podium(fights, results_map, athlete_repo):
    """
    Строим пьедестал на основе боёв и результатов.
    Логика IJF:
      1-е место  — победитель финала
      2-е место  — проигравший финала
      3-е место  — победители утешительных финалов (или полуфиналисты)
    """
    podium = []

    main_fights = [
        f
        for f in fights
        if not f.get("type_bracket") or f.get("type_bracket") == "MAIN"
    ]
    if not main_fights:
        return podium

    max_round = max((f.get("round") or f.get("round_number", 1)) for f in main_fights)
    final_fights = [
        f
        for f in main_fights
        if (f.get("round") or f.get("round_number", 1)) == max_round
    ]

    if not final_fights:
        return podium

    final = final_fights[0]
    result = results_map.get(final["id"])

    if result:
        winner_id = result.get("winner_id")
        white_id = (final.get("white_athlete") or {}).get("id")
        blue_id = (final.get("blue_athlete") or {}).get("id")
        loser_id = blue_id if winner_id == white_id else white_id

        if winner_id:
            podium.append(
                {
                    "pos": 1,
                    "athlete": _get_ath(winner_id, athlete_repo),
                    "club": _get_club(winner_id, athlete_repo),
                }
            )
        if loser_id:
            podium.append(
                {
                    "pos": 2,
                    "athlete": _get_ath(winner_id, athlete_repo),
                    "club": _get_club(winner_id, athlete_repo),
                }
            )

    cons_final_types = [
        str(BracketType.FINALIST_CONSOLATION_GROUP_A),
        str(BracketType.FINALIST_CONSOLATION_GROUP_B),
    ]
    cons_finals = [
        f for f in fights if str(f.get("type_bracket", "")) in cons_final_types
    ]

    for group_type in cons_final_types:
        group_fights = sorted(
            [f for f in cons_finals if str(f.get("type_bracket", "")) == group_type],
            key=lambda x: x.get("fight_number") or 0,
        )
        if not group_fights:
            continue
        last_fight = group_fights[-1]
        res = results_map.get(last_fight["id"])
        if res:
            winner_id = res.get("winner_id")
            if winner_id:
                data = athlete_repo.get_athlete_name_data(winner_id)
                if data:
                    data["id"] = winner_id
                podium.append(
                    {
                        "pos": 3,
                        "athlete": data or {},
                        "club": _get_club(winner_id, athlete_repo),
                    }
                )

    return sorted(podium, key=lambda x: (x["pos"], 0))


# ─────────────────────────────────────────────────────────────
# Хелпер: собрать данные одной tournament_category
# ─────────────────────────────────────────────────────────────
def _build_category_data(
    tc, category_repo, fight_repo, result_repo, athlete_repo, tournament_id
):
    cat = category_repo.get_category_by_id(tc.category_id)
    if not cat:
        return None

    tc_id = tc.tournament_category_id

    all_fights_orm = fight_repo.get_all_fights_by_tournament_category(tc_id)

    fights_dto = []
    for f in all_fights_orm:
        fights_dto.append(
            {
                "id": f.id,
                "round": f.round_number,
                "fight_number": f.fight_number,
                "type_bracket": f.type_bracket.value if f.type_bracket else "MAIN",
                "white_athlete": athlete_repo.get_athlete_by_fight(
                    f.white_athlete_id, f.id
                ),
                "tatami_number": f.tatami_number,
                "blue_athlete": athlete_repo.get_athlete_by_fight(
                    f.blue_athlete_id, f.id
                ),
            }
        )

    results_orm = result_repo.get_results_by_tournament(tournament_id, tc.category_id)
    results_dto = []
    results_map = {}
    for r in results_orm:
        dto = {
            "fight_id": r.fight_id,
            "winner_id": r.winner_id,
            "victory_type": r.victory_type.value if r.victory_type else "",
            "fight_duration": r.fight_duration,
        }
        results_dto.append(dto)
        results_map[r.fight_id] = dto

    podium = _build_podium(fights_dto, results_map, athlete_repo)

    competitors = len(
        set(
            ath_id
            for f in fights_dto
            for ath_id in [
                (f.get("white_athlete") or {}).get("id"),
                (f.get("blue_athlete") or {}).get("id"),
            ]
            if ath_id
        )
    )

    return {
        "id": cat.id,
        "name": cat.name,
        "tatami": tc.tatami_number if hasattr(tc, "tatami_number") else "—",
        "competitors": competitors,
        "fights": fights_dto,
        "results": results_dto,
        "podium": podium,
    }


# ─────────────────────────────────────────────────────────────
# Endpoint: GET /api/pdf/tournament/<tournament_id>
# ─────────────────────────────────────────────────────────────
@pdf_router.get("/tournament/{tournament_id}")
def get_tournament_pdf(tournament_id: int, category_id: int):
    try:
        # Если передан — генерируем PDF только для этой категории,
        # если нет — для всех категорий турнира.
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)
            if not tournament:
                return error_response("Турнир не найден", 404)

            category_repo = CategoryRepository(session)
            fight_repo = FightRepository(session)
            result_repo = ResultRepository(session)
            athlete_repo = AthleteRepository(session)

            tc_list = tournament_repo.get_tournament_categories(tournament_id)
            if not tc_list:
                return error_response("Категории не найдены", 404)

            # ── Фильтрация по category_id ──────────────────────────
            if category_id is not None:
                tc_list = [tc for tc in tc_list if tc.category_id == category_id]
                if not tc_list:
                    return error_response("Категория  не найдена в турнире", 404)
            # ───────────────────────────────────────────────────────

            categories_data = []
            for tc in tc_list:
                cat_data = _build_category_data(
                    tc,
                    category_repo,
                    fight_repo,
                    result_repo,
                    athlete_repo,
                    tournament_id,
                )
                if cat_data:
                    categories_data.append(cat_data)

            if not categories_data:
                return error_response("Нет данных для генерации PDF", 404)

            tournament_payload = {
                "tournament": {
                    "id": tournament.id,
                    "name": tournament.name,
                    "start_date": str(tournament.start_date)
                    if tournament.start_date
                    else "",
                    "city": tournament.city or "",
                    "country": tournament.country or "",
                },
                "categories": categories_data,
            }

        # Генерируем PDF вне сессии
        pdf_bytes = generate_tournament_pdf(tournament_payload)

        filename = (
            f"tournament_{tournament_id}_cat_{category_id}.pdf"
            if category_id is not None
            else f"tournament_{tournament_id}.pdf"
        )

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception:
        return error_response("Ошибка генерации PDF", 500)
