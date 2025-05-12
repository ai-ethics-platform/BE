from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Table, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base_class import Base


# 방 참가자 관계 테이블
room_participants = Table(
    "room_participants",
    Base.metadata,
    Column("room_id", Integer, ForeignKey("rooms.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("is_ready", Boolean, default=False),
    Column("joined_at", DateTime, default=datetime.utcnow),
)


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True, index=True)  # 방 입장 코드
    is_public = Column(Boolean, default=False)  # 공개/비공개 여부
    max_players = Column(Integer, default=3)  # 최대 참가자 수
    
    # 방 상태
    is_active = Column(Boolean, default=True)
    game_started = Column(Boolean, default=False)
    
    # 방장 정보
    creator_id = Column(Integer, ForeignKey("users.id"))
    creator = relationship("User", back_populates="rooms")
    
    # 참가자 관계
    participants = relationship("User", secondary=room_participants)
    
    # 게임 세션 관계
    game_sessions = relationship("GameSession", back_populates="room")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Map(Base):
    __tablename__ = "maps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)  # 가정/국가/세계
    description = Column(Text)
    unlock_condition = Column(String)  # 해금 조건
    
    # 게임 세션 관계
    game_sessions = relationship("GameSession", back_populates="map")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    
    # 관계 설정
    room_id = Column(Integer, ForeignKey("rooms.id"))
    room = relationship("Room", back_populates="game_sessions")
    
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="game_sessions")
    
    map_id = Column(Integer, ForeignKey("maps.id"))
    map = relationship("Map", back_populates="game_sessions")
    
    # 게임 정보
    ai_type = Column(String)  # AI 형태
    ai_name = Column(String)  # AI 이름
    
    # 게임 진행 상태
    current_round = Column(Integer, default=1)
    is_completed = Column(Boolean, default=False)
    
    # 선택 결과 저장
    individual_choices = Column(JSON, default={})  # 개인 선택 결과
    consensus_choices = Column(JSON, default={})  # 합의 선택 결과
    confidence_levels = Column(JSON, default={})  # 확신도 레벨
    
    # 엔딩 정보
    ending_id = Column(Integer, nullable=True)
    
    # 녹음 및 분석 관계
    audio_files = relationship("AudioFile", back_populates="game_session")
    transcriptions = relationship("Transcription", back_populates="game_session")
    ai_analyses = relationship("AIAnalysis", back_populates="game_session")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True) 