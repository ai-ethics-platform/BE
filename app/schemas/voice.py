from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# 음성 세션 생성 요청 스키마
class VoiceSessionCreate(BaseModel):
    room_code: str = Field(..., min_length=4, max_length=20, description="방 코드")


# 음성 세션 응답 스키마
class VoiceSession(BaseModel):
    id: int
    room_id: int
    session_id: str
    is_active: bool
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 음성 참가자 상태 스키마
class VoiceParticipant(BaseModel):
    id: int
    voice_session_id: int
    user_id: Optional[int] = None
    guest_id: Optional[str] = None
    nickname: str
    is_mic_on: bool
    is_speaking: bool
    is_connected: bool
    recording_file_path: Optional[str] = None
    recording_started_at: Optional[datetime] = None
    recording_ended_at: Optional[datetime] = None
    joined_at: datetime
    last_activity: datetime

    class Config:
        from_attributes = True


# 음성 상태 업데이트 요청 스키마
class VoiceStatusUpdate(BaseModel):
    session_id: str = Field(..., description="음성 세션 ID")
    is_mic_on: bool = Field(..., description="마이크 ON/OFF 상태")
    is_speaking: Optional[bool] = Field(False, description="말하는 중인지 여부")


# 음성 상태 업데이트 응답 스키마
class VoiceStatusResponse(BaseModel):
    participant: VoiceParticipant
    message: str = "음성 상태가 업데이트되었습니다."


# 음성 세션 참가 요청 스키마
class VoiceJoinRequest(BaseModel):
    session_id: str = Field(..., description="음성 세션 ID")
    nickname: str = Field(..., min_length=1, max_length=50, description="닉네임")


# 음성 세션 참가 응답 스키마
class VoiceJoinResponse(BaseModel):
    session: VoiceSession
    participant: VoiceParticipant
    message: str = "음성 세션에 참가했습니다."


# 음성 세션 퇴장 요청 스키마
class VoiceLeaveRequest(BaseModel):
    session_id: str = Field(..., description="음성 세션 ID")


# 음성 세션 퇴장 응답 스키마
class VoiceLeaveResponse(BaseModel):
    session_id: str
    message: str = "음성 세션에서 퇴장했습니다."


# 음성 세션 정보 조회 응답 스키마
class VoiceSessionInfo(BaseModel):
    session: VoiceSession
    participants: List[VoiceParticipant]
    total_participants: int


# 녹음 시작 요청 스키마
class RecordingStartRequest(BaseModel):
    session_id: str = Field(..., description="음성 세션 ID")


# 녹음 시작 응답 스키마
class RecordingStartResponse(BaseModel):
    participant: VoiceParticipant
    recording_file_path: str
    message: str = "녹음이 시작되었습니다."


# 녹음 종료 요청 스키마
class RecordingStopRequest(BaseModel):
    session_id: str = Field(..., description="음성 세션 ID")


# 녹음 종료 응답 스키마
class RecordingStopResponse(BaseModel):
    participant: VoiceParticipant
    recording_file_path: str
    duration: int
    message: str = "녹음이 종료되었습니다."


# 음성 녹음 업로드 요청 스키마
class RecordingUploadRequest(BaseModel):
    session_id: str = Field(..., description="음성 세션 ID")
    file_path: str = Field(..., description="업로드할 파일 경로")


# 음성 녹음 업로드 응답 스키마
class RecordingUploadResponse(BaseModel):
    recording_id: int
    file_path: str
    file_size: int
    message: str = "녹음 파일이 업로드되었습니다."


# WebSocket 메시지 타입
class WebSocketMessage(BaseModel):
    type: str = Field(..., description="메시지 타입")
    data: dict = Field(..., description="메시지 데이터")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# WebSocket 음성 상태 브로드캐스트 메시지
class VoiceStatusBroadcast(BaseModel):
    type: str = "voice_status_update"
    participant_id: int
    nickname: str
    is_mic_on: bool
    is_speaking: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# WebSocket 참가자 입장/퇴장 메시지
class ParticipantEvent(BaseModel):
    type: str = Field(..., description="이벤트 타입: join/leave")
    participant_id: int
    nickname: str
    timestamp: datetime = Field(default_factory=datetime.utcnow) 

class VoiceParticipant(BaseModel):
    id: int
    name: str
    is_speaking: bool