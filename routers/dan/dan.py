from fastapi.routing import APIRouter

from models.new_dan import DanNew
from repository.dan_repo import DanRepository
from routers.dan.schemas import DanCreateRequest, DanDTO, DanResponse
from utils.helpers import error_response

dans_bp = APIRouter(prefix="/api/dans", tags=["Dans"])


@dans_bp.get("/", status_code=200, response_model=DanResponse)
def get_dans():
    """Получить список данов"""
    try:
        with DanRepository() as dan_repo:
            dans = dan_repo.get_dans()

            result = []
            for dan in dans:
                result.append(DanDTO.from_dan(dan, dan_repo.get_athletes_count(dan.id)))

        return DanResponse(success=True, dans=result, total=len(result))

    except Exception:
        return error_response("Ошибка при получении данов", 500)


@dans_bp.post("/", status_code=201)
def create_dan(create_request: DanCreateRequest):
    """Создать новый дан"""
    try:
        with DanRepository() as dan_repo:
            existing_dan = dan_repo.get_dan_by_name(create_request.level.strip())
            if existing_dan:
                return error_response("Дан с таким уровнем уже существует", 400)

            dan = DanNew(
                level=create_request.level.strip(),
                description=create_request.description.strip()
                if create_request.description
                else None,
            )

            dan_id = dan_repo.create_dan(dan)
        if dan_id:
            return {"success": True, "message": "Дан успешно создан"}
        else:
            return error_response("Ошибка создания дана, попробуйте снова", 400)

    except Exception as e:
        return error_response("Ошибка добавление дана, попробуйте позже", 500)
