from datetime import date

from fastapi.routing import APIRouter
from models import CategoryNew
from models.Enums import translate_gender
from repository.category_repo import CategoryRepository
from routers.category.schemas import CreateCategoryRequest, UpdateCategoryRequest

categories_router = APIRouter(prefix="/api/categories", tags=["Categories"])


@categories_router.get("/")
async def get_categories(tournamentId: int):
    """Получить список категорий"""
    try:
        with CategoryRepository() as category_repo:
            categories = category_repo.get_categories(tournamentId)

            result = []
            for category in categories:
                tournament_ids = [
                    t.tournament_category_id for t in category.tournament_categories
                ]

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
                        "tournament_id": tournament_ids,
                    }
                )

        return {"success": True, "categories": result, "total": len(result)}

    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при получении категорий: {str(e)}",
        }


@categories_router.get("/{category_id}")
async def get_category(category_id: int):
    """Получить информацию о категории"""
    try:
        with CategoryRepository() as category_repo:
            category = category_repo.get_category_by_id(category_id)

        if category is None:
            return {"success": False, "message": "Категория не найдена"}

        return {
            "id": category.id,
            "name": category.name,
            "gender": category.gender.value,
            "min_weight": category.min_weight,
            "max_weight": category.max_weight,
            "min_age": category.min_year,
            "max_age": category.max_year,
            "athletes_count": category_repo.get_all_athletes(category.id),
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при получении категории: {str(e)}",
        }


@categories_router.get("/{category_id}/athletes")
async def get_category_athletes(category_id: int):
    """Получить участников категории"""
    try:
        with CategoryRepository() as category_repo:
            category = category_repo.get_category_by_id(category_id)
            if not category:
                return {"success": False, "message": "Категория не найдена"}

            athletes = []
            for athlete in category.athletes:
                athletes.append(
                    {
                        "id": athlete.id,
                        "full_name": f"{athlete.user.last_name} {athlete.user.first_name} {athlete.user.middle_name or ''}".strip(),
                        "club": athlete.club_id,
                        "age": athlete.age,
                        "rank": athlete.rank_id,
                    }
                )

        return {
            "success": True,
            "category": category.name,
            "athletes": athletes,
            "total": len(athletes),
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при получении участников категории: {str(e)}",
        }


@categories_router.post("/")
async def create_category(create_data: CreateCategoryRequest):
    """Создать новую категорию"""
    try:
        if not create_data.gender:
            return {"success": False, "message": "Обязательные поля: gender"}

        if create_data.min_weight > create_data.max_age != 0:
            return {"message": "Минемальный вес не может быть больше максимального"}

        # === Проверка веса ===
        if (
            create_data.max_weight != 0
            and create_data.min_weight > create_data.max_age != 0
        ):
            return {"message": "Минимальный вес не может быть больше максимального"}

        # === Проверка возраста (только годы) ===
        min_age = create_data.min_age
        max_age = create_data.max_age

        date_min = date(year=min_age, month=1, day=1)
        date_max = date(year=max_age, month=1, day=1)

        if max_age != 0 and date_min > date_max:
            return {
                "message": "Минимальный год не может быть больше максимального года"
            }

        under_or_over_weight = (
            f"-{create_data.max_age}"
            if create_data.max_age != 0
            else f"+{create_data.min_age}"
        )
        generate_name = f"{under_or_over_weight}кг, ПОЛ: {create_data.gender}, ГОДА:с {create_data.min_age} по {create_data.max_age}"

        with CategoryRepository() as category_repo:
            existing_category = category_repo.get_category_by_name(generate_name)
            if existing_category:
                return {"message": "Такая категория существует"}

            translate_gender_ = translate_gender(create_data.gender)
            category = CategoryNew(
                name=generate_name,
                gender=translate_gender_,
                min_weight=create_data.min_weight,
                max_weight=create_data.max_weight,
                min_year=create_data.min_age,
                max_year=create_data.max_age,
            )

            is_create = category_repo.create_category(category)

        if is_create:
            return (
                {
                    "success": True,
                    "message": f"Категория успешно создана {generate_name}",  # ← используем переменную!
                },
            )
        else:
            return {"success": False, "message": "Ошибка при сохранении категории"}

    except Exception as e:
        return {"success": False, "message": f"Ошибка при создании категории: {str(e)}"}


@categories_router.put("/{category_id}")
async def update_category(category_id: int, update_data: UpdateCategoryRequest):
    """Обновить категорию"""
    try:
        with CategoryRepository() as category_repo:
            is_update = category_repo.update_category(category_id, update_data)

        if is_update:
            return {
                "success": True,
                "message": "Категория успешно обновлена",
                "category_id": category_id,
            }
        else:
            return {"success": False, "message": "Ошибка при обновлении категории"}
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при обновлении категории: {str(e)}",
        }


@categories_router.delete("/{category_id}")
async def delete_category(category_id: int):
    """Удалить категорию"""
    try:
        with CategoryRepository() as category_repo:
            category = category_repo.get_category_by_id(category_id)

            if not category:
                return {"success": False, "message": "Категория не найдена"}

            is_delete = category_repo.delete_category(category)

        if is_delete:
            return {"success": True, "message": "Категория удалена"}
        else:
            return {"success": False, "message": "Ошибка при удалении категории"}

    except Exception as e:
        return {"success": False, "message": f"Ошибка при удалении категории: {str(e)}"}
