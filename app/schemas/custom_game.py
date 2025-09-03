from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class CustomGameCreate(BaseModel):
    teacher_name: str = Field(..., min_length=1, max_length=100)
    teacher_school: str = Field(..., min_length=1, max_length=200)
    teacher_email: str = Field(..., min_length=3, max_length=200)

    title: str = Field(..., min_length=1, max_length=100)
    representative_image_url: Optional[str] = None

    # Full game structure from editor
    data: Dict[str, Any] = Field(..., description="Game payload from editor UI")


class CustomGame(BaseModel):
    id: int
    code: str

    teacher_name: str
    teacher_school: str
    teacher_email: str

    title: str
    representative_image_url: Optional[str]
    data: Dict[str, Any]

    class Config:
        from_attributes = True


class CustomGameCreateResponse(BaseModel):
    code: str
    url: str



