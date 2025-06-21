from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    birthdate = Column(String(7), nullable=False)  # YYYY/MM 형식으로 변경
    gender = Column(String(10), nullable=False)  # "남", "여", "기타"
    education_level = Column(String(50), nullable=False)  # "고등학생", "대학생", "대학원생", "직장인", "기타"
    major = Column(String(50), nullable=False)  # "인문계열", "사회계열", "자연계열", "공학계열", "예술계열", "기타"
    
    is_active = Column(Boolean, default=True)
    is_guest = Column(Boolean, default=False)
    
    # 개인정보 및 음성 활용 동의
    data_consent = Column(Boolean, default=True)
    voice_consent = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_rooms = relationship("Room", back_populates="creator")
    room_participations = relationship("RoomParticipant", back_populates="user")
    voice_participations = relationship("VoiceParticipant", back_populates="user") 