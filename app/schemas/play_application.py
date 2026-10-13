from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# 사용자 데모 신청 요청
class PlayApplicationCreate(BaseModel):
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="성",
    )

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="이름",
    )

    email: EmailStr = Field(
        ...,
        description="신청자 이메일",
    )

    message: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="신청 시 남기는 메시지",
    )


# 신청 정보 공통 응답
class PlayApplicationResponse(BaseModel):
    id: int
    user_id: int

    last_name: str
    first_name: str
    email: EmailStr
    message: Optional[str] = None

    status: str

    applied_at: datetime
    approved_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True
        extra = "forbid"


# 현재 사용자의 승인 상태 조회 응답
class PlayApplicationStatusResponse(BaseModel):
    status: Optional[str] = None

    class Config:
        from_attributes = True
        extra = "forbid"


# 관리자 승인/거절 처리 후 응답
class PlayApplicationActionResponse(BaseModel):
    id: int
    status: str
    message: str