from fastapi import APIRouter, Query, status

from database.db import create_session
from repository.athlete_repo import AthleteRepository
from repository.club_repo import ClubRepository
from routers.club.schemas import (
    AssignAthletesRequest,
    ClubAthleteDTO,
    ClubAthletesResponse,
    ClubDTO,
    ClubListResponse,
    ClubResponse,
    CreateClubRequest,
    MessageResponse,
    UpdateClubRequest,
)
from utils.helpers import error_response
from utils.security import admin_depd

club_router = APIRouter(prefix="/api/clubs", tags=["Clubs"])


@club_router.get("/", response_model=ClubListResponse)
def get_clubs():
    with create_session() as session:
        club_repo = ClubRepository(session)
        athlete_repo = AthleteRepository(session)

        clubs = club_repo.get_clubs()
        result = [
            ClubDTO.from_club(
                club,
                athletes_count=athlete_repo.count_athletes_in_club(club.id),
            )
            for club in clubs
        ]

    return ClubListResponse(success=True, clubs=result, total=len(result))


@club_router.get("/search", dependencies=[admin_depd])
def search_athletes(
    last_name: str | None = None,
    first_name: str | None = None,
    middle_name: str | None = None,
    q: str | None = None,
    club_id: int | None = None,
):
    """Поиск спортсменов по ФИО"""
    try:
        name_query = {}
        if q:
            parts = q.strip().split()
            if len(parts) >= 1:
                name_query["last_name"] = parts[0]
            if len(parts) >= 2:
                name_query["first_name"] = parts[1]
            if len(parts) >= 3:
                name_query["middle_name"] = " ".join(parts[2:])
        else:
            if last_name:
                name_query["last_name"] = last_name
            if first_name:
                name_query["first_name"] = first_name
            if middle_name:
                name_query["middle_name"] = middle_name

        if not name_query:
            return error_response("Не переданы параметры поиска", 400)

        with create_session() as session:
            athlete_repo = AthleteRepository(session)
            athletes = athlete_repo.search_athletes_by_name(
                name_query=name_query, club_id=club_id
            )

            result = []
            for athlete in athletes:
                result.append(
                    {
                        "id": athlete.id,
                        "user_id": athlete.user.id,
                        "last_name": athlete.user.last_name or "Неизвестно",
                        "first_name": athlete.user.first_name or "Неизвестно",
                        "middle_name": athlete.user.middle_name or None,
                        "full_name": " ".join(
                            filter(
                                None,
                                [
                                    athlete.user.last_name or "",
                                    athlete.user.first_name or "",
                                    athlete.user.middle_name or "",
                                ],
                            )
                        ),
                        "birth_date": athlete.birth_date.isoformat()
                        if athlete.birth_date
                        else None,
                        "age": athlete.age,
                        "gender": athlete.gender,
                        "rank": athlete.rank.level if athlete.rank else None,
                        "license_number": athlete.license_number,
                        "medical_check": athlete.medical_check,
                        "insurance_number": athlete.insurance_number,
                        "is_active": athlete.is_active,
                        "club": {
                            "id": athlete.club.id,
                            "name": athlete.club.name,
                            "short_name": athlete.club.short_name,
                        }
                        if athlete.club
                        else None,
                    }
                )

        return {
            "success": True,
            "search_params": name_query or {"q": q},
            "athletes_count": len(result),
            "athletes": result,
        }

    except Exception as e:
        return error_response(f"Ошибка при поиске спортсменов: {str(e)}", 500)


@club_router.post(
    "/",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_club(create_club_request: CreateClubRequest):
    with create_session() as session:
        club_repo = ClubRepository(session)

        existing_club = club_repo.get_club_by_name(create_club_request.name.strip())
        if existing_club:
            return error_response("Клуб с таким названием уже существует", 400)

        is_created = club_repo.create_club(create_club_request)
        if not is_created:
            return error_response("Ошибка при сохранении в базу", 400)

    return MessageResponse(success=True, message="Клуб успешно создан")


@club_router.delete("/{club_id}", response_model=MessageResponse)
def delete_club(club_id: int):
    with create_session() as session:
        club_repo = ClubRepository(session)

        club = club_repo.get_club_by_id(club_id)
        if not club:
            return error_response(f"Клуб с ID {club_id} не найден", 404)

        club_name = club.name
        is_deleted = club_repo.delete_club(club_id)
        if not is_deleted:
            return error_response("Не удалось удалить клуб", 400)

    return MessageResponse(
        success=True,
        message=f"Клуб '{club_name}' успешно удалён, спортсмены отвязаны",
    )


@club_router.put("/{club_id}", response_model=ClubResponse)
def update_club(club_id: int, update_request: UpdateClubRequest):
    update_data = update_request.model_dump()

    if not update_data:
        return error_response("Не передано ни одно поле для обновления", 400)

    if "name" in update_data and not update_data["name"].strip():
        return error_response("Название клуба не может быть пустым", 400)

    with create_session() as session:
        club_repo = ClubRepository(session)

        club = club_repo.get_club_by_id(club_id)
        if not club:
            return error_response("Клуб не найден", 404)

        is_updated = club_repo.update_club(club_id, update_data)
        if not is_updated:
            return error_response("Не удалось обновить данные клуба", 400)

        updated_club = club_repo.get_club_by_id(club_id)
        club_dto = ClubDTO.from_club(updated_club)

    return ClubResponse(success=True, club=club_dto)


@club_router.get("/{club_id}/club-athletes/", response_model=ClubAthletesResponse)
def get_club_athletes(
    club_id: int,
    include_tournament_info: bool = Query(default=False),
    tournament_id: int | None = Query(default=None),
):
    with create_session() as session:
        club_repo = ClubRepository(session)

        club = club_repo.get_club_by_id(club_id)
        if not club:
            return error_response(f"Клуб с ID {club_id} не найден", 404)

        athlete_repo = AthleteRepository(session)
        athletes = athlete_repo.get_athletes_by_club_id(
            club_id=club_id,
            tournament_id=tournament_id,
            include_tournament_info=include_tournament_info,
        )

        result = []
        for athlete in athletes:
            athlete_data = {
                "id": athlete.id,
                "user_id": athlete.user_id,
                "last_name": athlete.user.last_name or "Неизвестно",
                "first_name": athlete.user.first_name or "Неизвестно",
                "middle_name": athlete.user.middle_name,
                "birth_date": athlete.birth_date,
                "age": athlete.age,
                "gender": athlete.gender,
                "rank": athlete.rank.level if athlete.rank else None,
                "license_number": athlete.license_number,
                "medical_check": athlete.medical_check,
                "insurance_number": athlete.insurance_number,
                "is_active": athlete.is_active,
            }

            if include_tournament_info:
                tournaments = []
                for registration in getattr(athlete, "registrations", []) or []:
                    tc = registration.tournament_category
                    if tc and tc.tournament:
                        tournaments.append(
                            {
                                "tournament_id": tc.tournament.id,
                                "tournament_name": tc.tournament.name,
                            }
                        )
                athlete_data["tournaments"] = tournaments

            result.append(ClubAthleteDTO(**athlete_data))

        return ClubAthletesResponse(
            success=True,
            club_id=club.id,
            club_name=club.name,
            athletes_count=len(result),
            athletes=result,
        )


@club_router.post("/{club_id}/assign-athletes", response_model=MessageResponse)
def assign_athletes(club_id: int, request: AssignAthletesRequest):
    with create_session() as session:
        club_repo = ClubRepository(session)

        club = club_repo.get_club_by_id(club_id)
        if not club:
            return error_response("Нет такого клуба", 404)

        club_repo.assign_athlete_to_club(
            club_id=club_id,
            athlete_ids=request.athlete_ids,
        )

    return MessageResponse(success=True, message="Участники добавлены в клуб")


@club_router.post("/{club_id}/unassign-athletes", response_model=MessageResponse)
def unassign_athletes(club_id: int, request: AssignAthletesRequest):
    with create_session() as session:
        club_repo = ClubRepository(session)

        club = club_repo.get_club_by_id(club_id)
        if not club:
            return error_response("Нет такого клуба", 404)

        club_repo.unassign_athletes_from_club(
            club_id=club_id,
            athlete_ids=request.athlete_ids,
        )

    return MessageResponse(success=True, message="Участники удалены из клуба")
