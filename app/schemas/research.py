"""
연구 데이터 분석 API 스키마
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================
# 기본 데이터 모델
# ============================================

class UserDataExport(BaseModel):
    """사용자 정보 export"""
    user_id: int
    username: str
    email: str
    birthdate: str
    gender: str
    education_level: str
    major: str
    data_consent: bool
    voice_consent: bool
    created_at: datetime


class RoundChoiceData(BaseModel):
    """라운드별 선택 데이터"""
    round_number: int
    choice: int
    subtopic: Optional[str] = None
    confidence: Optional[int] = None
    created_at: datetime


class ConsensusChoiceData(BaseModel):
    """합의 선택 데이터"""
    round_number: int
    choice: int
    subtopic: Optional[str] = None
    confidence: Optional[int] = None
    created_at: datetime


class VoiceRecordingData(BaseModel):
    """음성 녹음 데이터"""
    id: int
    user_id: Optional[int] = None
    guest_id: Optional[str] = None
    file_path: str
    file_size: Optional[int] = None
    duration: Optional[int] = None
    created_at: datetime
    is_processed: Optional[bool] = False


class VoiceSessionData(BaseModel):
    """음성 세션 데이터"""
    session_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    is_active: bool
    recordings: List[VoiceRecordingData] = []


class ParticipantData(BaseModel):
    """참가자 데이터"""
    participant_id: int
    nickname: str
    role_id: Optional[int] = None
    is_host: bool
    user_data: Optional[Dict[str, Any]] = None
    round_choices: List[RoundChoiceData] = []


class RoomDataExport(BaseModel):
    """Room 데이터 export"""
    room_id: int
    room_code: str
    title: str
    topic: str
    ai_type: Optional[int] = None
    ai_name: Optional[str] = None
    is_started: bool
    start_time: Optional[datetime] = None
    created_at: datetime
    participants: List[ParticipantData] = []
    consensus_choices: List[ConsensusChoiceData] = []
    voice_sessions: List[VoiceSessionData] = []


# ============================================
# API Response 모델
# ============================================

class ExperimentDataResponse(BaseModel):
    """전체 실험 데이터 export 응답"""
    rooms: List[RoomDataExport]
    total_count: int
    page: int
    page_size: int
    exported_at: datetime


class DataStatisticsResponse(BaseModel):
    """데이터 통계 응답"""
    total_users: int
    users_with_full_consent: int
    total_rooms: int
    total_started_rooms: int
    total_voice_recordings: int
    total_round_choices: int
    total_consensus_choices: int
    generated_at: datetime


class ParticipantDetailData(BaseModel):
    """참가자 상세 데이터"""
    participant_id: int
    nickname: str
    role_id: Optional[int] = None
    is_host: bool
    joined_at: datetime
    user_info: Optional[Dict[str, Any]] = None
    round_choices: List[RoundChoiceData] = []


class VoiceSessionDetailData(BaseModel):
    """음성 세션 상세 데이터"""
    session_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    recordings: List[VoiceRecordingData] = []


class RoomDetailResponse(BaseModel):
    """Room 상세 데이터 응답"""
    room_id: int
    room_code: str
    title: str
    topic: str
    ai_type: Optional[int] = None
    ai_name: Optional[str] = None
    is_started: bool
    start_time: Optional[datetime] = None
    created_at: datetime
    participants: List[ParticipantDetailData] = []
    consensus_choices: List[ConsensusChoiceData] = []
    voice_sessions: List[VoiceSessionDetailData] = []


# ============================================
# Request 모델
# ============================================

class DeleteTestDataRequest(BaseModel):
    """테스트 데이터 삭제 요청"""
    room_ids: Optional[List[int]] = Field(None, description="삭제할 room ID 리스트")
    user_ids: Optional[List[int]] = Field(None, description="삭제할 user ID 리스트 (주의해서 사용)")
    delete_voice_files: bool = Field(False, description="음성 파일도 삭제할지 여부")


class DeleteTestDataResponse(BaseModel):
    """테스트 데이터 삭제 응답"""
    deleted_rooms: int
    deleted_users: int
    deleted_voice_recordings: int
    message: str


# ============================================
# 분석 모델
# ============================================

class RoundChoiceAnalysis(BaseModel):
    """라운드 선택 분석"""
    round_number: int
    choice: int
    count: int
    avg_confidence: Optional[float] = None


class RoleChoiceAnalysis(BaseModel):
    """역할별 선택 분석"""
    role_id: Optional[int] = None
    choice: int
    count: int


class ChoiceAnalysisResponse(BaseModel):
    """선택 데이터 분석 응답"""
    round_choices: List[RoundChoiceAnalysis]
    role_choices: List[RoleChoiceAnalysis]
