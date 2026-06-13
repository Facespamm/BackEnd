from datetime import datetime

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter

from database.db import create_session
from models import AthleteNew, UserNew
from models.Enums import RoleName, translate_gender
from repository.athlete_repo import AthleteRepository
from repository.auth_repo import AuthRepository
from routers.athletes.schemas import (
    CreateAthleteByAdminRequest,
    CreateAthleteRequest,
    UpdateAthleteRequest,
)
from utils.annotation import PaginationDependency
from utils.helpers import error_response

athlete_router = APIRouter(prefix="/api/athletes", tags=["Athletes"])

# TODO - добавить пагинацию, коды выполнения и ошибок, логирование


@athlete_router.get("/{athlete_id}")
async def get_athlete_by_id(athlete_id: int):
    """Получить информацию об участнике"""
    try:
        with AthleteRepository() as athlete_repo:
            athlete = athlete_repo.get_athlete_by_id(athlete_id)

            if not athlete or athlete.is_active is False:
                return error_response("Участник не найден", 404)

            return {
                "success": True,
                "athlete": {
                    "id": athlete.id,
                    "first_name": athlete.user.first_name,
                    "last_name": athlete.user.last_name,
                    "middle_name": athlete.user.middle_name,
                    "birth_date": athlete.birth_date.isoformat(),
                    "age": athlete.age,
                    "gender": athlete.gender,
                    "club_id": athlete.club_id,
                    "club_name": athlete.club.name if athlete.club else None,
                    "rank": athlete.rank.level if athlete.rank else None,
                    "rank_id": athlete.rank_id,
                    "license_number": athlete.license_number,
                    "phone": athlete.user.phone,
                    "email": athlete.user.email,
                    "medical_check": athlete.medical_check,
                    "insurance_number": athlete.insurance_number,
                },
            }
    except Exception as e:
        return error_response(f"Ошибка при получении участника: {str(e)}", 500)


@athlete_router.get("/for_registration_on_club")
async def registration_on_club():
    with AthleteRepository() as athlete_repo:
        athletes = athlete_repo.get_athlete_for_registrations_on_club()

        result = [
            {
                "id": athlete.id,
                "last_name": athlete.user.last_name,
                "first_name": athlete.user.first_name,
                "patronymic": athlete.user.middle_name,
                "birth_date": athlete.birth_date,
                "age": athlete.age,
                "club_name": athlete.club.name if athlete.club else None,
                "gender": athlete.gender,
            }
            for athlete in athletes
        ]

    return {"message": True, "athletes": result}


@athlete_router.get("/")
async def get_athletes(
    pagination: PaginationDependency,
    club_id: int | None = None,
    search: str | None = None,
    tournament_id: int | None = None,
):
    """Получить список участников"""
    page = pagination.page
    page_size = pagination.per_page

    try:
        with AthleteRepository() as athlete_repo:
            basic_information = athlete_repo.get_basic_info(
                page, page_size, club_id, search, tournament_id
            )

        result = [
            {
                "id": athlete[0],
                "first_name": athlete[1],
                "last_name": athlete[2],
                "middle_name": athlete[3],
                "rank": athlete[4],
                "gender": athlete[5],
                "age": athlete[6],
            }
            for athlete in basic_information
        ]

        return {"success": True, "athletes": result, "total": len(result)}
    except Exception as e:
        return error_response(f"Ошибка при получении участников: {str(e)}", 500)


@athlete_router.get("/search-athlete")
async def search_athlete(
    last_name: str, first_name: str, middle_name: str, club_id: int
):
    """Поиск участника по ФИО для получения его ID"""
    try:
        # Проверяем, что хотя бы один параметр передан
        if not any([last_name, first_name, middle_name, club_id]):
            return error_response(
                "Укажите хотя бы один параметр поиска (last_name, first_name, middle_name или club_id)",
                400,
            )

        name_query = {
            "last_name": last_name,
            "first_name": first_name,
            "middle_name": middle_name,
        }

        with AthleteRepository() as athlete_repo:
            athletes = athlete_repo.search_athletes_by_name(name_query, club_id)

        result = [
            {
                "id": athlete.id,
                "user_id": athlete.user.id,
                "last_name": athlete.user.last_name,
                "first_name": athlete.user.first_name,
                "middle_name": athlete.user.middle_name,
            }
            for athlete in athletes
        ]

        return result

    except Exception as e:
        return error_response(f"Ошибка при поиске участника: {str(e)}", 500)


@athlete_router.post("/private/create-athlete-admin")
async def create_athlete_registration(create_athlete: CreateAthleteByAdminRequest):
    try:
        # 'password' поока убран, надо сделать через ссылку активации

        names = create_athlete.fullname.strip().split(" ")
        create_athlete.gender = translate_gender(create_athlete.gender)

        date_now = datetime.now()
        years = relativedelta(date_now, create_athlete.birth_date).years

        with create_session() as session:
            auth_repo = AuthRepository(session)
            existing_user = auth_repo.get_user_by_username(create_athlete.login)
            if existing_user:
                return error_response(
                    "Пользователь с таким логином уже существует",
                    400,
                )

            existing_email = auth_repo.get_user_by_email(create_athlete.email)
            if existing_email:
                return error_response("Email уже используется", 400)

            new_user = UserNew(
                username=create_athlete.login,
                password_hash="!",  # не валидный хэш #auth_repo.hash_password(data['password']),
                first_name=names[0] if len(names) > 0 else "",
                middle_name=names[1] if len(names) > 1 else "",
                last_name=names[2] if len(names) > 2 else "",
                email=create_athlete.email,
                phone=create_athlete.phone,
            )

            is_user_id = auth_repo.create_user(new_user)
            user_id = new_user.id if is_user_id is int else None

            if user_id is not int:
                return error_response("Не получилось создать пользователя", 500)

            new_athlete = AthleteNew(
                user_id=user_id,
                birth_date=create_athlete.birth_date,
                gender=create_athlete.gender,
                club_id=create_athlete.club_id,
                rank_id=create_athlete.rank_id,
                license_number=create_athlete.license_number,
                medical_check=create_athlete.medical_check,
                insurance_number=create_athlete.insurance_number,
                age=years,
                is_active=True,
            )
            athlete_repo = AthleteRepository(session)

            is_created = athlete_repo.create_athlete(new_athlete)

        if is_created:
            return {"message": "Вы создали участника"}
        else:
            return error_response("Не получилось создать пользователя", 500)
    except Exception as e:
        return error_response(f"Ошибка регистрации пользователя: {e}", 500)


@athlete_router.post("/{user_id}")
async def create_athlete(user_id: int, create_athlete: CreateAthleteRequest):
    """Создать нового участника"""
    try:
        if not user_id:
            return error_response("Нет такого пользователя", 404)

        with AthleteRepository() as athlete_repo:
            has_athlete = athlete_repo.has_athlete(user_id)

        if has_athlete:
            return error_response(
                "У этого пользователя уже есть профиль участника",
                400,
            )

        if create_athlete.gender:
            create_athlete.gender = translate_gender(create_athlete.gender)

        date_now = datetime.now()
        years = relativedelta(date_now, create_athlete.bith_date).years

        athlete = AthleteNew(
            id=None,
            user_id=user_id,
            birth_date=create_athlete.bith_date,
            gender=create_athlete.gender,
            club_id=create_athlete.club_id,
            rank_id=create_athlete.rank_id,
            license_number=create_athlete.license_number,  # необязательно
            medical_check=create_athlete.medical_check,
            insurance_number=create_athlete.insurance_number,  # необязательно
            age=years,
            is_active=True,
        )

        athlete_id = None

        with create_session() as session:
            auth_repo = AuthRepository(session)
            athlete_repo = AthleteRepository(session)

            role_id = auth_repo.get_role_id(RoleName.ATHLETE.value)
            auth_repo.update_user_role(user_id, role_id)
            athlete_is_added = athlete_repo.create_athlete(athlete)

            if athlete_is_added:
                session.flush()
                athlete_id = athlete.id
                session.commit()

        if not athlete_is_added:
            session.rollback()
            return error_response("Ошибка при сохранении участника", 500)

        return {
            "success": True,
            "message": "Участник успешно создан",
            "athlete_id": athlete_id,
            "user_id": user_id,
        }
    except Exception as e:
        return error_response(f"Ошибка при создании участника: {str(e)}", 500)


@athlete_router.put("/{athlete_id}")
async def update_athlete(athlete_id: int, updated_data: UpdateAthleteRequest):
    """Обновить информацию об участнике"""
    try:
        with AthleteRepository() as repo:
            athlete = repo.get_athlete_by_id(athlete_id)

            if not athlete or athlete.is_active is False:
                return error_response("Участник не найден", 404)

            is_updated = repo.update_athlete(athlete, updated_data)

        if is_updated:
            return {
                "success": True,
                "message": "Участник успешно обновлен",
                "athlete_id": athlete.id,
            }
        else:
            return error_response("Ошибка при сохранении", 500)
    except Exception as e:
        return error_response(f"Ошибка при обновлении участника: {str(e)}", 500)


@athlete_router.delete("/{athlete_id}")
async def delete_athlete(athlete_id: int):
    """Удалить участника (мягкое удаление)"""
    try:
        with AthleteRepository() as athlete_repo:
            athlete = athlete_repo.get_athlete_by_id(athlete_id)
            if not athlete or athlete.is_active is False:
                return error_response("Участник не найден", 404)

            # Мягкое удаление - помечаем как неактивного
            is_deleted = athlete_repo.delete_athlete(athlete)

        if is_deleted:
            return {"success": True, "message": "Участник удален"}
        else:
            return error_response("Ошибка при удалении", 500)
    except Exception as e:
        return error_response(f"Ошибка при удалении участника: {str(e)}", 500)
