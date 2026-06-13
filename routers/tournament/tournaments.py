from fastapi import APIRouter, Query

from database.db import create_session
from models.Enums import StatusTournament, StatusTournamentRegistration
from models.tournament_new import TournamentNew
from repository.athlete_repo import AthleteRepository
from repository.category_repo import CategoryRepository
from repository.tournament_repo import TournamentRepository
from routers.tournament.schemas import (
    AddAthletesRequest,
    TournamentCreateRequest,
    TournamentDTO,
    TournamentUpdateRequest,
)
from utils.annotation import PaginationDependency
from utils.helpers import error_response

tournaments_router = APIRouter(prefix="/api/tournaments", tags=["Tournaments"])


@tournaments_router.get("/", status_code=200)
def get_tournaments(
    pagination: PaginationDependency,
    status: StatusTournament | None = None,
    category_id: int | None = None,
    search: str | None = None,
):
    """Получить список всех турниров"""
    try:
        page = pagination.page
        per_page = pagination.per_page
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournaments = tournament_repo.get_all_tournaments(
                status, page, per_page, search, category_id
            )

            result = []
            for tournament in tournaments:
                athlete_count = tournament_repo.get_register_athlete_count(
                    tournament.id
                )
                result.append(TournamentDTO.from_tournament(tournament, athlete_count))

        return result

    except Exception:
        return error_response("Внутренняя ошибка сервера", 500)


@tournaments_router.get("/{tournament_id}", status_code=200)
def get_tournament(tournament_id: int):
    """Получить информацию о турнире"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)

            if not tournament:
                return error_response("Турнир не найден", 404)

            return TournamentDTO.from_tournament(
                tournament,
                athletes_count=tournament_repo.get_athlete_count(tournament_id),
            )

    except Exception:
        return error_response("Ошибка при получении информации о турнире", 500)


@tournaments_router.get("/{tournament_id}/preliminary_registrations")
def get_tournament_preliminary_registrations(tournament_id: int):
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)

            if not tournament:
                return error_response("Турнир не найден", 404)

            athletes = tournament_repo.get_preliminary_registrations(tournament_id)

            result = []
            for athlete_data in athletes:
                athlete = athlete_data["athlete"]
                result.append(
                    {
                        "athlete_id": athlete.id,
                        "first_name": athlete.user.first_name if athlete.user else None,
                        "last_name": athlete.user.last_name if athlete.user else None,
                        "gender": athlete.gender,
                        "birth_date": athlete.birth_date.isoformat()
                        if athlete.birth_date
                        else None,
                        "age": athlete.age,
                        "club_name": athlete.club.name if athlete.club else None,
                        "rank": athlete.rank.level if athlete.rank else None,
                    }
                )

        return {
            "success": True,
            "tournament_id": tournament_id,
            "athletes_count": len(result),
            "athletes": result,
        }
    except Exception as e:
        return error_response(f"Ошибка при получении атлетов турнира: {e}", 500)


@tournaments_router.get("/{tournament_id}/tatami")
def get_tournament_tatami(tournament_id: int):
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)

            if not tournament:
                return error_response("Нет такого турнира", 404)

            tatamis = tournament_repo.get_tatami_by_tournament(tournament_id)
            athlete_repo = AthleteRepository(session)
            tatami_dto = [
                {
                    "tatami_number": tatami.tatami_number,
                    "status": tatami.status.value,
                    "fight": {
                        "white_athlete": athlete_repo.get_athlete_name_data(
                            tatami.fight.white_athlete_id
                        ),
                        "blue_athlete": athlete_repo.get_athlete_name_data(
                            tatami.fight.blue_athlete_id
                        ),
                    }
                    if tatami.fight_id and tatami.fight
                    else None,
                }
                for tatami in tatamis
            ]

        return tatami_dto

    except Exception as e:
        return error_response(f"Ошибка вывода {e}", 500)


@tournaments_router.get("/{tournament_id}/athletes")
def get_tournament_athletes_after_weighed(
    tournament_id: int,
    category_id: int | None = Query(default=None),
):
    """Получить список зарегистрированных атлетов на турнир"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)

            if not tournament:
                return error_response("Турнир не найден", 404)

            if category_id:
                athletes = tournament_repo.get_weighed_athletes(
                    tournament_id, category_id
                )
            else:
                athletes = tournament_repo.get_preliminary_registrations(
                    tournament_id, status=StatusTournamentRegistration.REGISTERED
                )

            result = []
            for athlete_data in athletes:
                athlete = athlete_data["athlete"]
                # category = athlete_data['category']
                result.append(
                    {
                        "athlete_id": athlete.id,
                        "first_name": athlete.user.first_name if athlete.user else None,
                        "last_name": athlete.user.last_name if athlete.user else None,
                        "middle_name": athlete.user.middle_name
                        if athlete.user
                        else None,
                        "gender": athlete.gender,
                        "birth_date": athlete.birth_date.isoformat()
                        if athlete.birth_date
                        else None,
                        "age": athlete.age,
                        "club_name": athlete.club.name if athlete.club else None,
                        "rank": athlete.rank.level if athlete.rank else None,
                        # 'category_id': category.id,
                        # 'category_name': category.name
                    }
                )

        return {
            "success": True,
            "tournament_id": tournament_id,
            "athletes_count": len(result),
            "athletes": result,
        }

    except Exception as e:
        return error_response(f"Ошибка при получении атлетов турнира: {e}", 500)


@tournaments_router.get("/{tournament_id}/categories")
def get_tournament_categories(tournament_id: int):
    """Получить категории турнира"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)

            if not tournament:
                return error_response("Турнир не найден", 404)

            category_repo = CategoryRepository(session)
            result = []
            for tournament_category in tournament.tournament_categories:
                category = tournament_category.category
                result.append(
                    {
                        "id": category.id,
                        "name": category.name,
                        "gender": category.gender.value,
                        "min_weight": category.min_weight,
                        "max_weight": category.max_weight,
                        "min_age": category.min_year,
                        "max_age": category.max_year,
                        "athletes_count": category_repo.get_all_athletes(category.id),
                    }
                )

        return result

    except Exception as e:
        return error_response(f"Ошибка при получении категорий: {e}", 500)


@tournaments_router.post("/")
def create_tournament(create_request: TournamentCreateRequest):
    """Создать новый турнир"""
    try:
        tournament_new = TournamentNew(
            name=create_request.name,
            description=create_request.description,
            start_date=create_request.start_date,
            end_date=create_request.end_date,
            venue=create_request.venue,
            city=create_request.city,
            country=create_request.country,
            tatami_count=create_request.tatami_count,
            has_consolation_fights=create_request.has_consalation,
        )

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_id = tournament_repo.create_tournament(tournament_new)
            if not tournament_id:
                return error_response("Ошибка создание турнира, попробуйте позже", 500)

            tournament = tournament_repo.get_tournament_by_id(tournament_id)
            if not tournament:
                return error_response("Ошибка при получении созданного турнира", 500)
            how_categories_assigned = []
            for category in create_request.list_category:
                if category <= 0:
                    continue
                how_categories_assigned.append(
                    tournament_repo.assign_category_tournament(
                        category, tournament.id, create_request.has_consalation
                    )
                )

            tournament_repo.create_tatami(tournament.id, tournament.tatami_count)

        return {
            "success": True,
            "message": "Турнир успешно создан"
            if len(how_categories_assigned) == len(create_request.list_category)
            else f"Турнир создан, но не все категории были прикреплены. Было прикрепленн {len(how_categories_assigned)} из {len(create_request.list_category)} категорий",
            "tournament_id": tournament_id,
        }
    except Exception as e:
        print(e)
        return error_response(
            "Ошибка при прикреплении категорий к турниру или создании татами",
            500,
        )


@tournaments_router.put("/{tournament_id}")
def update_tournament(tournament_id: int, request: TournamentUpdateRequest):
    """Обновить информацию о турнире"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)

            if not tournament:
                return error_response("Турнир не найден", 404)

            is_updated = tournament_repo.update_tournament(tournament, request)
            if is_updated:
                return {
                    "success": True,
                    "message": "Турнир успешно обновлен",
                    "tournament": {
                        "id": tournament.id,
                        "name": tournament.name,
                        "status": tournament.status.value,
                    },
                }

            return error_response(
                "Ошибка при обновлении турнира, попробуйте сново", 400
            )

    except Exception:
        return error_response("Ошибка обновления турнираб попробуйте позже", 500)


@tournaments_router.post("/{tournament_id}/add-club")
def add_club_to_tournament(
    tournament_id: int,
    club_id: int | None = Query(default=None),
):
    """Добавить клуб к турниру"""
    if not club_id:
        return error_response("Не передан клуб", 400)

    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            is_added = tournament_repo.add_club_to_tournament(tournament_id, club_id)

            if is_added == 0:
                return error_response("Все устники клуба уже участвуют в нем", 200)

        return {
            "success": True,
            "message": "Клуб добавлен к турниру",
        }

    except Exception as e:
        return error_response(f"Ошибка при добавлении клуба к турниру: {e}", 500)


@tournaments_router.post("/{tournament_id}/add-athletes")
def add_athletes_to_tournament(tournament_id: int, request: AddAthletesRequest):
    """Добавить участников к турниру"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            added_athletes = 0
            for athlete_id in request.athlete_ids:
                is_add = tournament_repo.add_athlete_to_tournament(
                    tournament_id, athlete_id
                )
                if is_add:
                    added_athletes += 1

        return {
            "success": True,
            "message": "Участники добавлены к турниру",
            "count_added": added_athletes,
        }

    except Exception as e:
        return error_response(f"Ошибка при добавлении участников к турниру: {e}", 500)


@tournaments_router.post("/{tournament_id}/add-category")
def add_category_to_tournament(
    tournament_id: int, category_id: int, has_consolation: bool = Query(default=False)
):
    """Добавить категорию к турниру"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            is_added = tournament_repo.assign_category_tournament(
                category_id, tournament_id, has_consolation
            )

            if is_added:
                return {
                    "success": True,
                    "message": f"Категория {category_id} добавлена к турниру {tournament_id}",
                }

            return error_response(
                f"Ошибка при добавлении категории {category_id} к турниру {tournament_id}",
                400,
            )

    except Exception as e:
        return error_response(f"Ошибка при добавлении категории к турниру: {e}", 500)


@tournaments_router.delete("/{tournament_id}/remove-athlete/{athlete_id}")
def remove_athlete_from_tournament(tournament_id: int, athlete_id: int):
    """Удалить участника из турнира"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            is_removed = tournament_repo.remove_athlete_from_tournament(
                tournament_id, athlete_id
            )

            if is_removed:
                return {
                    "success": True,
                    "message": f"Атлет {athlete_id} удален из турнира {tournament_id}",
                }

            return error_response(
                f"Ошибка при удалении атлета {athlete_id} из турнира {tournament_id}",
                400,
            )

    except Exception as e:
        return error_response(f"Ошибка при удалении атлета из турнира: {e}", 500)


@tournaments_router.delete("/{tournament_id}/remove-club/{club_id}")
def remove_club_from_tournament(tournament_id: int, club_id: int):
    """Удалить клуб из турнира"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            is_removed = tournament_repo.remove_club_from_tournament(
                tournament_id, club_id
            )

            if is_removed:
                return {
                    "success": True,
                    "message": f"Клуб {club_id} удален из турнира {tournament_id}",
                }

            return error_response(
                f"Ошибка при удалении клуба {club_id} из турнира {tournament_id}",
                400,
            )

    except Exception as e:
        return error_response(f"Ошибка при удалении клуба из турнира: {e}", 500)


@tournaments_router.delete("/{tournament_id}/remove-category/{category_id}")
def remove_category_from_tournament(tournament_id: int, category_id: int):
    """Удалить категорию из турнира"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            is_removed = tournament_repo.remove_category_from_tournament(
                tournament_id, category_id
            )

            if is_removed:
                return {
                    "success": True,
                    "message": f"Категория {category_id} удалена из турнира {tournament_id}",
                }

            return error_response(
                f"Ошибка при удалении категории {category_id} из турнира {tournament_id}",
                400,
            )

    except Exception as e:
        return error_response(f"Ошибка при удалении категории из турнира: {e}", 500)


@tournaments_router.delete("/{tournament_id}")
def delete_tournament(tournament_id: int):
    """Удалить турнир"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)

            if not tournament:
                return error_response("Турнир не найден", 404)

            if tournament_repo.delete_tournament(tournament):
                return {"success": True, "message": "Турнир удален"}

            return error_response("Ошибка при удалении турнира", 400)

    except Exception as e:
        return error_response(f"Ошибка при удалении турнира: {e}", 500)
