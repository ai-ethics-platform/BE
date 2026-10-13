from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class PlayApplication(Base):
    __tablename__ = "play_applications"

    id = Column(Integer, primary_key=True, index=True)

    # 신청한 회원
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    # 신청 시 입력 정보
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    message = Column(Text, nullable=True)

    # 신청 상태: pending / approved / rejected
    status = Column(String(20), default="pending", nullable=False)

    # 신청 및 상태 변경 시간
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # User 모델과 연결
    user = relationship("User", back_populates="play_application")