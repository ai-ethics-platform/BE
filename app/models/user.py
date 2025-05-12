from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    birthdate = Column(String)  # 형식: YYYY/MM/DD
    gender = Column(String)  # 남/녀/기타
    education_level = Column(String)  # 초등학생/중학생/고등학생/대학생/대학원생/직장인/기타
    major = Column(String, nullable=True)  # 전공 (해당하는 경우)
    
    is_active = Column(Boolean, default=True)
    is_guest = Column(Boolean, default=False)
    
    # 개인정보 및 음성 활용 동의
    data_consent = Column(Boolean, default=True)
    voice_consent = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    rooms = relationship("Room", back_populates="creator")
    game_sessions = relationship("GameSession", back_populates="user")
    audio_files = relationship("AudioFile", back_populates="user")
    
    # 사용자 통계
    games_played = Column(Integer, default=0)
    maps_unlocked = Column(Integer, default=0) 