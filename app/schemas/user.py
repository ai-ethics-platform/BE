from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

# 정규식 패턴
USERNAME_PATTERN = r'^[a-zA-Z0-9_]{4,20}$'
BIRTHDATE_PATTERN = r'^\d{4}/\d{2}$'  # YYYY/MM 형식으로 변경

# 교육 수준 옵션
EDUCATION_LEVELS = [
    "초등학생", "중학생", "고등학생", 
    "대학생", "대학원생", "직장인", "교사", "기타"
]

# 성별 옵션
GENDER_OPTIONS = ["남", "여", "기타"]

# 전공 계열 옵션
MAJOR_CATEGORIES = [
    "자연계열", "공학계열", "인문계열", 
    "사회계열", "예술계열", "교육계열", "기타"
]

# 학력 옵션
EDUCATION_OPTIONS = ["초등학생", "중학생", "고등학생", "대학생", "대학원생", "직장인", "교사", "기타"]

# 전공 옵션
MAJOR_OPTIONS = ["인문계열", "사회계열", "자연계열", "공학계열", "예술계열", "교육계열", "기타"]

# 공통 속성
class UserBase(BaseModel):
    username: str = Field(pattern=USERNAME_PATTERN)
    email: str = Field(pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    birthdate: str = Field(pattern=BIRTHDATE_PATTERN)
    gender: str = Field(pattern=f"^({'|'.join(GENDER_OPTIONS)})$")
    education_level: str = Field(pattern=f"^({'|'.join(EDUCATION_OPTIONS)})$")
    major: Optional[str] = Field(default=None, description="전공 계열 (대학생/대학원생만 필수)")
    is_active: Optional[bool] = True

    @field_validator('gender')
    def validate_gender(cls, v):
        if v not in GENDER_OPTIONS:
            raise ValueError(f'성별은 {", ".join(GENDER_OPTIONS)} 중 하나여야 합니다')
        return v

    @field_validator('education_level')
    def validate_education_level(cls, v):
        if v not in EDUCATION_LEVELS:
            raise ValueError(f'학년 단계는 {", ".join(EDUCATION_LEVELS)} 중 하나여야 합니다')
        return v

    @field_validator('major')
    def validate_major(cls, v, info):
        values = info.data
        # 대학생/대학원생만 전공 필수
        if values.get('education_level') in ['대학생', '대학원생'] and not v:
            raise ValueError('대학생/대학원생은 전공을 선택해야 합니다')
        # 그 외에는 미선택 허용. 선택했다면 유효값만 허용
        if v and v not in MAJOR_CATEGORIES:
            raise ValueError(f'전공은 {", ".join(MAJOR_CATEGORIES)} 중 하나여야 합니다')
        return v


# 사용자 생성 시 필요한 추가 속성
class UserCreate(UserBase):
    password: str = Field(min_length=8)
    data_consent: bool = Field(..., description="데이터 수집 동의")
    voice_consent: bool = Field(..., description="음성 녹음 동의")


# 로그인용 스키마
class UserLogin(BaseModel):
    username: str
    password: str


# 사용자 정보 업데이트
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    birthdate: Optional[str] = Field(None, pattern=BIRTHDATE_PATTERN)
    gender: Optional[str] = None
    education_level: Optional[str] = None
    major: Optional[str] = None
    data_consent: Optional[bool] = None
    voice_consent: Optional[bool] = None

    @field_validator('gender')
    def validate_gender(cls, v):
        if v and v not in GENDER_OPTIONS:
            raise ValueError(f'성별은 {", ".join(GENDER_OPTIONS)} 중 하나여야 합니다')
        return v

    @field_validator('education_level')
    def validate_education_level(cls, v):
        if v and v not in EDUCATION_LEVELS:
            raise ValueError(f'학년 단계는 {", ".join(EDUCATION_LEVELS)} 중 하나여야 합니다')
        return v

    @field_validator('major')
    def validate_major(cls, v, info):
        values = info.data
        if values.get('education_level') in ['대학생', '대학원생'] and not v:
            raise ValueError('대학생/대학원생은 전공을 선택해야 합니다')
        if v and v not in MAJOR_CATEGORIES:
            raise ValueError(f'전공은 {", ".join(MAJOR_CATEGORIES)} 중 하나여야 합니다')
        return v


# 동의 정보 업데이트
class ConsentUpdate(BaseModel):
    data_consent: bool
    voice_consent: bool


# DB에서 읽어온 사용자 정보
class UserInDB(UserBase):
    id: int
    is_active: bool
    is_guest: bool
    data_consent: bool
    voice_consent: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# API 응답용 사용자 정보
class User(UserInDB):
    pass


# 사용자 통계 정보
class UserStats(BaseModel):
    user_id: int
    
    class Config:
        from_attributes = True


# 아이디 중복 확인
class UsernameCheck(BaseModel):
    username: str
    available: Optional[bool] = None


# 아이디 찾기용 스키마
class FindUsernameRequest(BaseModel):
    email: EmailStr
    birthdate: str = Field(pattern=BIRTHDATE_PATTERN)
    gender: str

    @field_validator('gender')
    def validate_gender(cls, v):
        if v not in GENDER_OPTIONS:
            raise ValueError(f'성별은 {", ".join(GENDER_OPTIONS)} 중 하나여야 합니다')
        return v 