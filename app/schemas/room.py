from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Room 생성 요청 스키마
class RoomCreatePublic(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="방 제목")
    description: Optional[str] = Field(None, max_length=500, description="방 설명")
    topic: str = Field(..., description="플레이 주제")
    custom_room_code: Optional[str] = Field(
        None,
        min_length=6,
        max_length=6,
        pattern="^\\d{6}$",
        description="사용자 지정 방 코드 (6자리 숫자, 없으면 랜덤 생성)"
    )


# 비공개 방 생성 요청 스키마
class RoomCreatePrivate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="방 제목")
    description: Optional[str] = Field(None, max_length=500, description="방 설명")
    topic: str = Field(..., description="플레이 주제")
    custom_room_code: Optional[str] = Field(
        None,
        min_length=6,
        max_length=6,
        pattern="^\\d{6}$",
        description="사용자 지정 방 코드 (6자리 숫자, 없으면 랜덤 생성)"
    )


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


# 역할 배정 상태 조회 스키마
class RoleAssignmentStatus(BaseModel):
    room_code: str = Field(..., description="방 코드")
    is_roles_assigned: bool = Field(..., description="모든 참가자에게 역할이 배정되었는지 여부")
    assignments: List[RoleAssignment] = Field(..., description="역할 배정 결과 목록 (모든 참가자에게 배정된 경우에만)")
    total_participants: int = Field(..., description="총 참가자 수")
    assigned_participants: int = Field(..., description="역할이 배정된 참가자 수")


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
    room_code: str = Field(
        ..., 
        min_length=6, 
        max_length=6, 
        pattern="^\\d{6}$",
        description="방 입장 코드 (6자리 숫자)"
    )
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
    room_code: str = Field(
        ..., 
        min_length=6, 
        max_length=6, 
        pattern="^\\d{6}$",
        description="방 입장 코드 (6자리 숫자)"
    )


# 준비 상태 변경 응답 스키마
class RoomReadyResponse(BaseModel):
    participant: RoomParticipant
    room: Room
    game_starting: bool = Field(..., description="게임이 시작되는지 여부")
    start_time: Optional[datetime] = Field(None, description="게임 시작 시간 (3초 후)")
    message: str = "준비 상태가 변경되었습니다."


# 방 상태 초기화 요청 스키마 (테스트용)
class RoomResetRequest(BaseModel):
    room_code: str = Field(
        ..., 
        min_length=6, 
        max_length=6, 
        pattern="^\\d{6}$",
        description="방 입장 코드 (6자리 숫자)"
    )


# 방 상태 초기화 응답 스키마 (테스트용)
class RoomResetResponse(BaseModel):
    room: Room
    message: str = "방 상태가 초기화되었습니다."


# 방 나가기 요청 스키마
class RoomLeaveRequest(BaseModel):
    room_code: str = Field(
        ..., 
        min_length=6, 
        max_length=6, 
        pattern="^\\d{6}$",
        description="방 입장 코드 (6자리 숫자)"
    )


# 방 나가기 응답 스키마
class RoomLeaveResponse(BaseModel):
    room_code: str
    player_count: int = Field(..., description="남은 플레이어 수")
    room_deleted: bool = Field(..., description="방이 삭제되었는지 여부")
    new_host: Optional[dict] = Field(None, description="새로운 방장 정보 (방장이 바뀐 경우)")
    game_started: bool = Field(..., description="게임이 시작된 상태인지 여부")
    requires_lobby_redirect: bool = Field(..., description="대기실로 리다이렉트가 필요한지 여부")
    message: str = "방에서 나갔습니다."


# AI 형태 저장 요청
class AiTypeSelectRequest(BaseModel):
    room_code: str = Field(..., description="방 코드")
    ai_type: int = Field(..., ge=1, le=3, description="AI 형태 (1: 로봇, 2: 중간, 3: 사람)")


# AI 형태 조회 응답
class AiTypeSelectResponse(BaseModel):
    room_code: str
    ai_type: int


# AI 이름 저장 요청
class AiNameRequest(BaseModel):
    room_code: str = Field(..., description="방 코드")
    ai_name: str = Field(..., min_length=1, max_length=100, description="AI 이름")


# AI 이름 조회 응답
class AiNameResponse(BaseModel):
    room_code: str
    ai_name: str 

# 라운드 개인 선택 제출 요청 스키마
class RoundChoiceRequest(BaseModel):
    round_number: int = Field(..., ge=1, description="라운드 번호")
    choice: int = Field(..., ge=1, le=4, description="선택지 (1~4)")
    subtopic: Optional[str] = Field(None, description="서브토픽")

# 개별 확신도 제출 요청 스키마
class IndividualConfidenceRequest(BaseModel):
    round_number: int = Field(..., ge=1, description="라운드 번호")
    confidence: int = Field(..., ge=1, le=5, description="확신도 (1~5)")
    subtopic: Optional[str] = Field(None, description="서브토픽")

# 합의 선택 요청 스키마
class ConsensusChoiceRequest(BaseModel):
    round_number: int = Field(..., ge=1, description="라운드 번호")
    choice: int = Field(..., ge=1, le=4, description="선택지 (1~4)")
    subtopic: Optional[str] = Field(None, description="서브토픽")

# 합의 선택에 대한 확신도 제출 요청 스키마
class ConsensusConfidenceRequest(BaseModel):
    round_number: int = Field(..., ge=1, description="라운드 번호")
    confidence: int = Field(..., ge=1, le=5, description="확신도 (1~5)")
    subtopic: Optional[str] = Field(None, description="서브토픽")

# 선택 상태 응답 스키마
class ChoiceStatusResponse(BaseModel):
    round_number: int
    room_code: str
    participants: List[dict] = Field(..., description="참가자별 선택 완료 현황")
    all_completed: bool = Field(..., description="모든 참가자가 선택을 완료했는지 여부")
    consensus_completed: bool = Field(..., description="합의 선택이 완료되었는지 여부")
    can_proceed: bool = Field(..., description="다음 단계로 진행 가능한지 여부")
    consensus_choice: Optional[int] = Field(None, description="합의 선택된 선택지 (1~4)")

# 선택 제출 응답 스키마
class ChoiceSubmitResponse(BaseModel):
    room_code: str
    round_number: int
    choice: int
    message: str = "선택이 성공적으로 제출되었습니다."

# 확신도 제출 응답 스키마
class ConfidenceSubmitResponse(BaseModel):
    room_code: str
    round_number: int
    confidence: int
    message: str = "확신도가 성공적으로 제출되었습니다."

# 합의 선택 제출 응답 스키마
class ConsensusSubmitResponse(BaseModel):
    room_code: str
    round_number: int
    choice: int
    message: str = "합의 선택이 성공적으로 제출되었습니다." 

# 페이지 동기화 관련 스키마들
class PageArrivalRequest(BaseModel):
    room_code: str = Field(..., description="방 코드")
    page_number: int = Field(..., ge=1, description="도착한 페이지 번호")
    user_identifier: str = Field(..., description="사용자 식별자 (user_123 또는 guest_abc 형태)")


class PageArrivalResponse(BaseModel):
    room_code: str
    page_number: int
    arrived_users: int = Field(..., description="해당 페이지에 도착한 사용자 수")
    total_required: int = Field(..., description="방의 총 사용자 수")
    all_arrived: bool = Field(..., description="모든 사용자가 도착했는지 여부")
    message: str = "페이지 도착이 기록되었습니다."


class PageSyncStatus(BaseModel):
    room_code: str
    page_number: int
    arrived_users: int = Field(..., description="해당 페이지에 도착한 사용자 수")
    total_required: int = Field(..., description="방의 총 사용자 수")
    all_arrived: bool = Field(..., description="모든 사용자가 도착했는지 여부")
    can_proceed: bool = Field(..., description="다음 단계로 진행 가능한지 여부")
    arrived_user_list: List[str] = Field(..., description="도착한 사용자들의 식별자 목록")


class PageSyncRequest(BaseModel):
    room_code: str = Field(..., description="방 코드")
    page_number: int = Field(..., ge=1, description="동기화할 페이지 번호")


class PageSyncResponse(BaseModel):
    room_code: str
    page_number: int
    sync_signal: str = Field(..., description="동기화 신호 타입 (three_next 등)")
    message: str = "페이지 동기화 신호가 전송되었습니다." 