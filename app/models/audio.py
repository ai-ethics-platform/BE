from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)  # 바이트 단위
    duration = Column(Integer, nullable=True)  # 초 단위
    
    # 관계 설정
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="audio_files")
    
    game_session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=True)
    game_session = relationship("GameSession", back_populates="audio_files")
    
    room_id = Column(Integer, nullable=True)
    round_id = Column(Integer, nullable=True)
    
    # 전사 관계
    transcription = relationship("Transcription", back_populates="audio_file", uselist=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    language = Column(String, default="ko-KR")
    
    # 관계 설정
    audio_file_id = Column(Integer, ForeignKey("audio_files.id"), unique=True)
    audio_file = relationship("AudioFile", back_populates="transcription")
    
    game_session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=True)
    game_session = relationship("GameSession", back_populates="transcriptions")
    
    # AI 분석 관계
    ai_analysis = relationship("AIAnalysis", back_populates="transcription", uselist=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    
    # 분석 내용
    analysis = Column(JSON)  # 분석 결과 JSON 형태로 저장
    feedback = Column(Text)  # 피드백 텍스트
    
    # 관계 설정
    transcription_id = Column(Integer, ForeignKey("transcriptions.id"), unique=True)
    transcription = relationship("Transcription", back_populates="ai_analysis")
    
    game_session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=True)
    game_session = relationship("GameSession", back_populates="ai_analyses")
    
    created_at = Column(DateTime, default=datetime.utcnow) 