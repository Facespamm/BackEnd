from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import update

from database.db import create_session
from models.new_associations import AthleteRegistration, TournamentCategory
from models.new_athlete import AthleteNew
from models.weighing_new import WeighingNew
from repository.athlete_repo import AthleteRepository
from repository.category_repo import CategoryRepository
from repository.tournament_repo import TournamentRepository
from repository.weight_repo import WeightRepository
from routers.weighing.schemas import (
    ChangeCategoryRequest,
    CreateWeighingRequest,
    UpdateWeighingRequest,
    WeighingDTO,
    WeighingFilterParams,
)
from utils.helpers import error_response

weighing_router = APIRouter(prefix="/api/weighing", tags=["Weighing"])


@weighing_router.get("/")
def get_weighings(params: Annotated[WeighingFilterParams, Depends()]):
    """Получить список взвешиваний"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(
                params.tournament_id,
                params.category_id,
            )
            if not tournament_category:
                return error_response("Нет такой категории в турнире", 404)

            weighing_repo = WeightRepository(session)
            athlete_repo = AthleteRepository(session)
            category_repo = CategoryRepository(session)

            weighings = weighing_repo.get_weights(
                tournament_category.tournament_category_id,
                params.athlete_id,
            )

            result = []
            for weighing in weighings or []:
                athlete = athlete_repo.get_athlete_by_id(weighing.athlete_id)
                athlete_name = _athlete_name(athlete)
                category = category_repo.get_category_by_id(weighing.weight_category)
                tournament_name = (
                    tournament_repo.get_tournament_name_by_tournament_category(
                        weighing.tournament_category_id
                    )
                )

                result.append(
                    WeighingDTO.from_weighing(
                        weighing,
                        athlete_name=athlete_name or "Атлет не найден",
                        category=category,
                        tournament_name=tournament_name,
                        status=_is_within_weight_category_limits(weighing),
                    ).model_dump()
                )

        return {"success": True, "weighings": result, "total": len(result)}

    except Exception as e:
        return error_response(f"Ошибка при получении взвешиваний: {str(e)}", 500)


@weighing_router.patch("/{weighing_id}/toggle-validation")
def toggle_weighing_validation(weighing_id: int):
    try:
        with create_session() as session:
            weighing_repo = WeightRepository(session)
            weighing = weighing_repo.get_weight(weighing_id)
            if not weighing:
                return error_response("Взвешивание не найдено", 404)

            is_change = weighing_repo.change_weighing_validation(weighing_id)
            is_valid = weighing.is_valid
            status_display = _is_within_weight_category_limits(weighing)

        if is_change:
            return {
                "success": True,
                "message": f'Статус изменен на {"валидно" if is_valid else "невалидно"}',
                "is_valid": is_valid,
                "status_display": status_display,
            }

        return error_response("Не получилось обновить статус", 500)

    except Exception as e:
        return error_response(f"Ошибка при изменении статуса: {str(e)}", 500)


@weighing_router.put("/{weighing_id}")
def update_weighing(weighing_id: int, data: UpdateWeighingRequest):
    try:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return error_response("Нет данных для изменения", 400)

        with create_session() as session:
            weighing_repo = WeightRepository(session)
            weighing = weighing_repo.get_weight(weighing_id)
            if not weighing:
                return error_response("Взвешивание не найдено", 404)

            if "weight" in update_data:
                category_repo = CategoryRepository(session)
                category = category_repo.get_category_by_weight(weighing_id)
                if category and not _weight_fits_category(update_data["weight"], category):
                    return error_response(
                        f"Вес не подходит для такой категории {category.name}",
                        400,
                    )

            is_update = weighing_repo.update_weighing_information(
                weighing_id,
                update_data,
            )
            weight_category = weighing.weight_category
            is_valid = weighing.is_valid

        if is_update:
            return {
                "success": True,
                "message": "Взвешивание успешно обновлено",
                "weight_category": weight_category,
                "is_valid": is_valid,
            }

        return error_response("Не получилось обновить данные взвешивания", 500)

    except Exception as e:
        return error_response(f"Ошибка при обновлении взвешивания: {str(e)}", 500)


@weighing_router.post("/", status_code=201)
def create_weighing(data: CreateWeighingRequest):
    """Создать запись о взвешивании"""
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            athlete_repo = AthleteRepository(session)
            weighing_repo = WeightRepository(session)

            tournament_category = tournament_repo.get_tournament_category(
                data.tournament_id,
                data.category_id,
            )
            if not tournament_category:
                return error_response("Турнир не найден", 404)

            athlete = athlete_repo.get_athlete_by_id(data.athlete_id)
            if not athlete:
                return error_response("Участник не найден", 404)

            is_valid, correct_category_name = _is_valid_for_category(
                data.model_dump(),
                tournament_category,
                athlete,
                session,
            )

            if not is_valid:
                message = (
                    "Атлет не подходит для выбранной категории. "
                    f"Рекомендуемая категория: {correct_category_name}"
                    if correct_category_name
                    else "Не удалось определить подходящую категорию для атлета"
                )
                return error_response(message, 400)

            category_repo = CategoryRepository(session)
            category = category_repo.get_category_by_name(correct_category_name)
            if not category:
                return error_response("Подходящая категория не найдена", 404)

            weighing = WeighingNew(
                tournament_category_id=tournament_category.tournament_category_id,
                athlete_id=data.athlete_id,
                weight=data.weight,
                notes=data.notes,
                weight_category=category.id,
                is_valid=is_valid,
            )
            is_added = weighing_repo.create_weighting(weighing)
            has_assign_tournament = (
                tournament_repo.assign_athletes_tournament_after_weighting(
                    tournament_category.tournament_category_id,
                    athlete.id,
                )
            )

            if not is_added or not has_assign_tournament:
                return error_response("Ошибка создания взвешивания участника", 500)

            weighing_id = weighing.id
            weight_category = weighing.weight_category

        return {
            "success": True,
            "message": "Взвешивание успешно записано",
            "weighing_id": weighing_id,
            "weight_category": weight_category,
        }

    except Exception as e:
        return error_response(f"Ошибка при создании записи взвешивания: {str(e)}", 500)


@weighing_router.post("/{tournament_id}/change-category")
def change_category(tournament_id: int, data: ChangeCategoryRequest):
    try:
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            athlete_repo = AthleteRepository(session)

            tournament = tournament_repo.get_tournament_by_id(tournament_id)
            if not tournament:
                return error_response("Нет такого турнира", 404)

            category_repo = CategoryRepository(session)
            category = category_repo.get_category_by_id(data.category_id)
            if not category:
                return error_response("Нет такой категории", 400)

            tournament_category = tournament_repo.get_tournament_category(
                tournament.id,
                category.id,
            )
            if not tournament_category:
                return error_response("Нет такой категории в турнире", 404)

            athlete = athlete_repo.get_athlete_by_id(data.athlete_id)
            if not athlete:
                return error_response("Участник не найден", 404)

            existing = (
                session.query(AthleteRegistration.athlete_id)
                .filter_by(
                    tournament_category_id=tournament_category.tournament_category_id,
                    athlete_id=data.athlete_id,
                )
                .first()
            )

            is_valid, _ = _is_valid_for_category(
                data.model_dump(),
                tournament_category,
                athlete,
                session,
            )

            if existing and is_valid:
                return {"message": "Участник находится в правильной категории"}

            session.execute(
                update(AthleteRegistration)
                .where(
                    AthleteRegistration.athlete_id == athlete.id,
                    AthleteRegistration.tournament_category_id
                    == tournament_category.tournament_category_id,
                )
                .values(
                    athlete_id=data.athlete_id,
                    tournament_category_id=tournament_category.tournament_category_id,
                )
            )
            session.commit()
            category_name = category.name

        return {"message": f"Участник перенесен в категорию {category_name}"}

    except Exception as e:
        return error_response(f"Ошибка выполнения {str(e)}", 500)


@weighing_router.delete("/{weight_id}")
def delete_weighing(weight_id: int):
    try:
        with WeightRepository() as weight_repo:
            is_deleted = weight_repo.delete_weighting(weight_id)
            if is_deleted:
                return {"success": True, "message": "Взвешивание удалено"}

        return error_response("Не получилось удалить взвешивание", 500)

    except Exception as e:
        return error_response(f"Ошибка выполнения {str(e)}", 500)


def _athlete_name(athlete) -> str | None:
    if not athlete or not athlete.user:
        return None
    return (
        f"{athlete.user.first_name} "
        f"{athlete.user.last_name} "
        f"{athlete.user.middle_name or ''}"
    ).strip()


def _is_within_weight_category_limits(weighing: WeighingNew) -> bool:
    tc = weighing.tournament_categories
    if not tc or not tc.category:
        return False
    return _weight_fits_category(weighing.weight, tc.category)


def _weight_fits_category(weight: float, category) -> bool:
    if category.min_weight is None:
        return False
    if category.max_weight is None:
        return weight >= category.min_weight
    return category.min_weight <= weight <= category.max_weight


def _is_valid_for_category(
    data: dict,
    tournament_category: TournamentCategory,
    athlete: AthleteNew,
    session,
):
    """Проверяет соответствие атлета категории. Использует переданную сессию."""
    tournament_repo = TournamentRepository(session)
    category_repo = CategoryRepository(session)

    categories = tournament_repo.get_categories(tournament_category.tournament_id)
    if not categories:
        raise Exception("Нет категорий за турнир")

    matched_category_id = 0
    for category in categories:
        age_ok = category.min_year <= athlete.birth_date.year <= category.max_year
        gender = athlete.gender.value if hasattr(athlete.gender, "value") else athlete.gender
        gender_ok = category.gender.name == gender or category.gender.value == gender
        if not (age_ok and gender_ok):
            continue

        if _weight_fits_category(data["weight"], category):
            matched_category_id = category.id
            break

    if matched_category_id == 0:
        raise Exception("Нет подходящей категории в турнире")

    category = category_repo.get_category_by_id(matched_category_id)
    if category is None:
        return False, None

    is_valid = data["category_id"] == matched_category_id
    return is_valid, category.name
