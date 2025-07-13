from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
import secrets
import string


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    topic = Column(String(50), nullable=False)  # 플레이 주제
    is_public = Column(Boolean, default=True, nullable=False)
    allow_random_matching = Column(Boolean, default=True, nullable=False)  # 랜덤 배정 허용 여부
    max_players = Column(Integer, default=3, nullable=False)  # 기본값을 3으로 변경
    current_players = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_started = Column(Boolean, default=False, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)  # 게임 시작 예정 시간
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # 게스트도 방 생성 가능
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    ai_type = Column(Integer, nullable=True)  # 1, 2, 3 중 하나. 최초 1회만 저장
    ai_name = Column(String(100), nullable=True)  # AI 이름. 최초 1회만 저장

    # Relationships
    creator = relationship("User", back_populates="created_rooms")
    participants = relationship("RoomParticipant", back_populates="room")
    voice_sessions = relationship("VoiceSession", back_populates="room")

    @classmethod
    def generate_room_code(cls) -> str:
        """6자리 숫자만으로 랜덤 방 코드 생성"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))


class RoomParticipant(Base):
    __tablename__ = "room_participants"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 게스트는 null
    guest_id = Column(String(50), nullable=True)  # 게스트 ID
    nickname = Column(String(50), nullable=False)
    is_ready = Column(Boolean, default=False, nullable=False)
    is_host = Column(Boolean, default=False, nullable=False)  # 방장 여부
    role_id = Column(Integer, nullable=True)  # 역할 ID (1: 요양보호사, 2: 가족, 3: AI 개발자)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    room = relationship("Room", back_populates="participants")
    user = relationship("User", back_populates="room_participations") 

# 라운드별 개인 선택 저장
class RoundChoice(Base):
    __tablename__ = "round_choices"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    participant_id = Column(Integer, ForeignKey("room_participants.id"), nullable=False)
    choice = Column(Integer, nullable=False)  # 1~4
    confidence = Column(Integer, nullable=True)  # 1~5 확신도
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("Room")
    participant = relationship("RoomParticipant")

# 라운드별 합의 선택 저장
class ConsensusChoice(Base):
    __tablename__ = "consensus_choices"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    choice = Column(Integer, nullable=False)  # 1~4
    confidence = Column(Integer, nullable=True)  # 1~5 확신도
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("Room") 