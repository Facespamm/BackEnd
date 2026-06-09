"""
Вспомогательные функции для системы
"""

import math

from fastapi.responses import JSONResponse


def calculate_rounds(participants_count):
    """
    Расчет количества раундов для сетки
    """
    if participants_count <= 0:
        return 0

    return math.ceil(math.log2(participants_count))


def error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        content={"success": False, "message": message},
        status_code=status_code,
    )
