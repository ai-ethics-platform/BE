from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Room 생성 요청 스키마
class RoomCreatePublic(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="방 제목")
    description: Optional[str] = Field(None, max_length=500, description="방 설명")
    topic: str = Field(..., description="플레이 주제")
    allow_random_matching: bool = Field(True, description="랜덤 배정 허용 여부")
    custom_room_code: Optional[str] = Field(None, min_length=4, max_length=20, description="사용자 지정 방 코드 (allow_random_matching이 false일 때 사용)")
    max_players: int = Field(3, ge=3, le=3, description="플레이어 수 (고정: 3명)")


# 비공개 방 생성 요청 스키마
class RoomCreatePrivate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="방 제목")
    description: Optional[str] = Field(None, max_length=500, description="방 설명")
    topic: str = Field(..., description="플레이 주제")
    allow_random_matching: bool = Field(True, description="랜덤 배정 허용 여부")
    custom_room_code: Optional[str] = Field(None, min_length=4, max_length=20, description="사용자 지정 방 코드 (allow_random_matching이 false일 때 사용)")
    max_players: int = Field(3, ge=3, le=3, description="플레이어 수 (고정: 3명)")


# Room 참가자 스키마
class RoomParticipant(BaseModel):
    id: int
    user_id: Optional[int] = None
    guest_id: Optional[str] = None
    nickname: str
    is_ready: bool
    is_host: bool
    role_id: Optional[int] = None
    joined_at: datetime

    class Config:
        from_attributes = True


# 역할 배정 응답 스키마
class RoleAssignment(BaseModel):
    player_id: str = Field(..., description="플레이어 ID (user_id 또는 guest_id)")
    role_id: int = Field(..., description="역할 ID (1: 요양보호사, 2: 가족, 3: AI 개발자)")
    role_name: str = Field(..., description="역할 이름")


# 역할 배정 결과 스키마
class RoleAssignmentResult(BaseModel):
    assignments: List[RoleAssignment] = Field(..., description="역할 배정 결과 목록")
    message: str = Field("역할이 성공적으로 배정되었습니다.", description="응답 메시지")


# Room 응답 스키마
class Room(BaseModel):
    id: int
    room_code: str
    title: str
    description: Optional[str] = None
    topic: str
    is_public: bool
    allow_random_matching: bool
    max_players: int
    current_players: int
    is_active: bool
    is_started: bool
    start_time: Optional[datetime] = None
    created_by: int
    created_at: datetime
    participants: List[RoomParticipant] = []

    class Config:
        from_attributes = True


# Room 생성 응답 스키마
class RoomCreateResponse(BaseModel):
    room: Room
    message: str = "공개 방이 성공적으로 생성되었습니다."


# Room 목록 조회용 간단한 스키마
class RoomSummary(BaseModel):
    id: int
    room_code: str
    title: str
    topic: str
    current_players: int
    max_players: int
    is_started: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Room 입장 요청 스키마
class RoomJoinRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=50, description="게임 내 닉네임")


# 플레이 주제 목록
AVAILABLE_TOPICS = [
    "자율주행차 윤리",
    "AI 채용 시스템",
    "의료 AI 진단",
    "AI 감시 시스템",
    "AI 콘텐츠 생성",
    "AI 교육 시스템"
]

# 역할 정의
ROLE_DEFINITIONS = {
    1: "요양보호사",
    2: "가족",
    3: "AI 개발자"
}

# 방 코드로 입장하는 요청 스키마
class RoomJoinByCode(BaseModel):
    room_code: str = Field(..., min_length=4, max_length=20, description="방 입장 코드")
    nickname: str = Field(..., min_length=1, max_length=50, description="게임 내 닉네임")


# 방 ID로 입장하는 요청 스키마 (공개 방 목록에서 선택)
class RoomJoinById(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=50, description="게임 내 닉네임")


# 방 입장 응답 스키마 (방 정보 포함)
class RoomJoinResponse(BaseModel):
    participant: RoomParticipant
    room: Room
    message: str = "방에 성공적으로 입장했습니다."


# 준비 상태 변경 요청 스키마
class RoomReadyRequest(BaseModel):
    pass  # 헤더의 토큰으로 사용자 식별


# 준비 상태 변경 응답 스키마
class RoomReadyResponse(BaseModel):
    participant: RoomParticipant
    room: Room
    game_starting: bool = Field(..., description="게임이 시작되는지 여부")
    start_time: Optional[datetime] = Field(None, description="게임 시작 시간 (3초 후)")
    message: str = "준비 상태가 변경되었습니다."


# 방 상태 초기화 요청 스키마 (테스트용)
class RoomResetRequest(BaseModel):
    pass


# 방 상태 초기화 응답 스키마 (테스트용)
class RoomResetResponse(BaseModel):
    room: Room
    message: str = "방 상태가 초기화되었습니다."


# 방 나가기 요청 스키마
class RoomLeaveRequest(BaseModel):
    pass  # 헤더의 토큰으로 사용자 식별


# 방 나가기 응답 스키마
class RoomLeaveResponse(BaseModel):
    room_code: str
    player_count: int = Field(..., description="남은 플레이어 수")
    room_deleted: bool = Field(..., description="방이 삭제되었는지 여부")
    new_host: Optional[dict] = Field(None, description="새로운 방장 정보 (방장이 바뀐 경우)")
    game_started: bool = Field(..., description="게임이 시작된 상태인지 여부")
    requires_lobby_redirect: bool = Field(..., description="대기실로 리다이렉트가 필요한지 여부")
    message: str = "방에서 나갔습니다." 