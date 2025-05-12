from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


# 공통 속성
class UserBase(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    birthdate: Optional[str] = None  # 형식: YYYY/MM/DD
    gender: Optional[str] = None  # 남/녀/기타
    education_level: Optional[str] = None  # 초등학생/중학생/고등학생/대학생/대학원생/직장인/기타
    major: Optional[str] = None  # 전공 (해당하는 경우)
    is_active: Optional[bool] = True


# 사용자 생성 시 필요한 추가 속성
class UserCreate(UserBase):
    username: str
    password: str
    email: EmailStr
    birthdate: str
    gender: str
    education_level: str
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('아이디는 영문자와 숫자만 포함해야 합니다')
        return v
    
    @validator('birthdate')
    def validate_birthdate_format(cls, v):
        try:
            year, month, day = v.split('/')
            if not (len(year) == 4 and len(month) == 2 and len(day) == 2):
                raise ValueError()
            if not (year.isdigit() and month.isdigit() and day.isdigit()):
                raise ValueError()
        except:
            raise ValueError('생년월일은 YYYY/MM/DD 형식이어야 합니다')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        if v not in ['남', '녀', '기타']:
            raise ValueError('성별은 남/녀/기타 중 하나여야 합니다')
        return v
    
    @validator('education_level')
    def validate_education_level(cls, v):
        valid_levels = ['초등학생', '중학생', '고등학생', '대학생', '대학원생', '직장인', '기타']
        if v not in valid_levels:
            raise ValueError('유효하지 않은 학력 단계입니다')
        return v


# 사용자 정보 업데이트
class UserUpdate(UserBase):
    password: Optional[str] = None


# 동의 정보 업데이트
class ConsentUpdate(BaseModel):
    data_consent: bool
    voice_consent: bool


# DB에서 읽어온 사용자 정보
class UserInDBBase(UserBase):
    id: int
    is_guest: bool
    data_consent: bool
    voice_consent: bool
    created_at: datetime
    
    class Config:
        orm_mode = True


# API 응답용 사용자 정보
class User(UserInDBBase):
    pass


# 사용자 통계 정보
class UserStats(BaseModel):
    user_id: int
    games_played: int
    maps_unlocked: int
    
    class Config:
        orm_mode = True


# 아이디 중복 확인
class UsernameCheck(BaseModel):
    username: str
    available: Optional[bool] = None 