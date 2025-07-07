# app/models/voice.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class VoiceSession(Base):
    """음성 대화 세션"""
    __tablename__ = "voice_sessions"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    session_id = Column(String(50), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    room = relationship("Room", back_populates="voice_sessions")
    participants = relationship("VoiceParticipant", back_populates="voice_session")


class VoiceParticipant(Base):
    """음성 대화 참가자 상태"""
    __tablename__ = "voice_participants"

    id = Column(Integer, primary_key=True, index=True)
    voice_session_id = Column(Integer, ForeignKey("voice_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 게스트는 null
    guest_id = Column(String(50), nullable=True)  # 게스트 ID
    nickname = Column(String(50), nullable=False)
    
    # 음성 상태
    is_mic_on = Column(Boolean, default=False, nullable=False)
    is_speaking = Column(Boolean, default=False, nullable=False)
    is_connected = Column(Boolean, default=True, nullable=False)
    
    # 녹음 관련
    recording_file_path = Column(String(255), nullable=True)  # 녹음 파일 경로
    recording_started_at = Column(DateTime(timezone=True), nullable=True)
    recording_ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # 메타데이터
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    voice_session = relationship("VoiceSession", back_populates="participants")
    user = relationship("User", back_populates="voice_participations")


class VoiceRecording(Base):
    """음성 녹음 기록"""
    __tablename__ = "voice_recordings"

    id = Column(Integer, primary_key=True, index=True)
    voice_session_id = Column(Integer, ForeignKey("voice_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 게스트는 null
    guest_id = Column(String(50), nullable=True)  # 게스트 ID
    
    # 녹음 정보
    file_path = Column(String(255), nullable=False)  # 실제 파일 경로
    file_size = Column(Integer, nullable=True)  # 파일 크기 (bytes)
    duration = Column(Integer, nullable=True)  # 녹음 시간 (초)
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    is_processed = Column(Boolean, default=False, nullable=False)  # 음성 분석 완료 여부

    # Relationships
    voice_session = relationship("VoiceSession")
    user = relationship("User") 