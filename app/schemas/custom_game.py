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


# Sectional payloads (page-wise updates)
class OpeningUpdate(BaseModel):
    opening: list[str] = Field(..., min_length=1, description="오프닝 멘트 배열(3~5문장)")


class RoleItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)


class RolesUpdate(BaseModel):
    roles: list[RoleItem] = Field(..., min_length=3, max_length=3, description="3개의 역할")
    background: Optional[str] = Field(default=None, description="역할 공통 배경 설명")


class TitleUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)


class TitleResponse(BaseModel):
    title: str


class RolesResponse(BaseModel):
    roles: list[RoleItem]
    background: Optional[str] = None


class RoleImagesResponse(BaseModel):
    urls: dict


class DilemmaOptions(BaseModel):
    agree_label: str = Field(..., min_length=1)
    disagree_label: str = Field(..., min_length=1)


class DilemmaUpdate(BaseModel):
    situation: list[str] = Field(..., min_length=1, description="상황 문장 배열(3~5문장)")
    question: str = Field(..., min_length=1, description="질문 1문장")
    options: DilemmaOptions


class FlipsUpdate(BaseModel):
    agree_texts: list[str] = Field(..., min_length=1, description="동의 선택 시 3~5문장")
    disagree_texts: list[str] = Field(..., min_length=1, description="비동의 선택 시 3~5문장")


class EndingUpdate(BaseModel):
    agree: str = Field(..., min_length=1, description="동의 선택 엔딩")
    disagree: str = Field(..., min_length=1, description="비동의 선택 엔딩")



