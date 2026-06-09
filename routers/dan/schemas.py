from pydantic import BaseModel


class DanDTO(BaseModel):
    id: int
    level: str
    description: str
    athletes_count: int = 0

    @classmethod
    def from_dan(cls, dan, athletes_count):
        return cls(
            id=dan.id,
            level=dan.level,
            description=dan.description,
            athletes_count=athletes_count,
        )


class DanResponse(BaseModel):
    success: bool
    dans: list[DanDTO]
    total: int


class DanCreateRequest(BaseModel):
    level: str
    description: str | None = None
