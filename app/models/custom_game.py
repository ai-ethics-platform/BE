from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint

from app.db.base_class import Base


class CustomGame(Base):
    __tablename__ = "custom_games"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)

    # Teacher info
    teacher_name = Column(String(100), nullable=False)
    teacher_school = Column(String(200), nullable=False)
    teacher_email = Column(String(200), nullable=False)

    # Game metadata
    title = Column(String(100), nullable=False)
    representative_image_url = Column(String(500), nullable=True)

    # Entire game payload as JSON string (to keep flexibility)
    data = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("code", name="uq_custom_game_code"),
    )



