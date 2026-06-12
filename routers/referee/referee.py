from fastapi.routing import APIRouter

from models import RefereeNew
from models.Enums import text_to_referee_level
from repository.figth_repo import FightRepository
from repository.referee_repo import RefereeRepository
from repository.tournament_repo import TournamentRepository
from routers.referee.schemas import (
    AsignReferees,
    CreateRefereeRequest,
    RefereeDTO,
    UpdateRefereRequest,
)
from utils.helpers import error_response
from utils.security import admin_depd, admin_or_referee_depd

referee_router = APIRouter(prefix="/api/referee", tags=["Referee"])
referee_repo = RefereeRepository()


@referee_router.get("/", dependencies=[admin_or_referee_depd])
def get_referees():
    try:
        referees = referee_repo.get_referees()

        results = [RefereeDTO.from_referee(referee) for referee in referees]

        return {"referees": results, "count_referees": len(results)}

    except Exception as e:
        print(f"Error in get_referees: {e}")
        return error_response("Проблеммы с получением судей", 500)


@referee_router.get("/{referee_id}", dependencies=[admin_or_referee_depd])
def get_referee(referee_id: int):
    try:
        referee = referee_repo.get_referee(referee_id)

        referee_dto = RefereeDTO.from_referee(referee)

        return {"referee": referee_dto}
    except Exception as e:
        print(f"Error in get_referee: {e}")
        return error_response("Ошибка получение судьи", 500)


@referee_router.post("/", status_code=201, dependencies=[admin_or_referee_depd])
def create_referee(create_data: CreateRefereeRequest):
    try:
        certificat_level = text_to_referee_level(create_data.certification_level)

        if not certificat_level:
            return error_response("Нет такого сертификата", 404)

        new_referee = RefereeNew(
            first_name=create_data.first_name,
            last_name=create_data.last_name,
            middle_name=create_data.middle_name,
            email=create_data.email,
            phone=create_data.phone,
            certification_level=certificat_level,
        )

        is_added = referee_repo.create_referee(new_referee)

        if is_added:
            return {"message": "Судья создан", "referee_id": new_referee.id}
        else:
            return error_response("Судья не создан", 500)

    except Exception as e:
        print(f"Error in create_referee: {e}")
        return error_response("Прогблемма создание судьи", 500)


@referee_router.put("/{referee_id}", dependencies=[admin_depd])
def update_referee(referee_id: int, data: UpdateRefereRequest):
    try:
        referee = referee_repo.get_referee(referee_id)
        if not referee:
            return error_response("Не найден такой судья", 404)

        certification_level = text_to_referee_level(data.certification_level)
        if not certification_level:
            return error_response("Нет такого сертификата", 404)

        update_data = data.model_dump()
        update_data["certification_level"] = certification_level

        is_updated = referee_repo.update_referee(referee, update_data)

        if is_updated:
            return {"message": "Данные обнавленны"}

        return error_response("Не получилось обновить", 500)

    except Exception as e:
        print(f"Error in update_referee: {e}")
        return error_response("Ошибка обнавления", 500)


@referee_router.post(
    "/{tournament_id}/assign_to-fights", dependencies=[admin_or_referee_depd]
)
def assign_referees_to_fights(tournament_id: int, category: int, data: AsignReferees):
    try:
        tournament_repo = TournamentRepository()
        tournament_category = tournament_repo.get_tournament_category(
            tournament_id, category
        )

        if not tournament_category:
            return error_response("Нет такой категории в турнире", 404)

        fight_repo = FightRepository()
        figths = fight_repo.get_fight_by_tournament(
            tournament_category.tournament_category_id
        )

        if not figths:
            return error_response("В этой категории нет боев", 404)
        referees = data.referees
        for fight in figths:
            fight_repo.assign_referee(referees[0], fight.id, "Главный")
            fight_repo.assign_referee(referees[1], fight.id, "Второй")
            fight_repo.assign_referee(referees[2], fight.id, "Третий")

        return {"message": "Судьи назначены на бои"}
    except Exception as e:
        print(f"Error in assign_referees_to_fights: {e}")
        return error_response("Ошибка назначения судей на бои", 500)


@referee_router.delete("/{referee_id}", dependencies=[admin_depd])
def delete_referee(referee_id: int):
    try:
        referee = referee_repo.get_referee(referee_id)
        if not referee:
            return error_response("Нет такого судьи", 404)

        is_deleted = referee_repo.delete_referee(referee.id)

        if is_deleted:
            return {"message": "Судья удален"}
        else:
            return error_response("Ошибка удаления судьи", 400)
    except Exception as e:
        print(f"Error in delete_referee: {e}")
        return error_response("Ошибка удаления", 500)
