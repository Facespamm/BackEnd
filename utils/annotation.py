from typing import Annotated

from fastapi import Depends
from fastapi.param_functions import Query
from pydantic.main import BaseModel


class PaginationParams(BaseModel):
    per_page: Annotated[int, Query(1, ge=1, le=50)]
    page_size: Annotated[int, Query(1, ge=1)]


PaginationDependency = Annotated[PaginationParams, Depends()]
