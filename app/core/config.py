# app/core/config.py
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    # CORS 설정
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str = "AI 윤리게임"
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "ai_ethics_db"
    
    # Database URL
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # SQL 로그 설정 (개발 환경에서만 활성화)
    SQL_ECHO: bool = False
    
    # 데이터베이스 연결 풀 설정
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str):
            return v
        values = info.data
        return f"mysql+aiomysql://{values['DB_USER']}:{values['DB_PASSWORD']}@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}"
    
    # OpenAI API 설정
    OPENAI_API_KEY: str = ""
    
    # 챗봇 단계별 프롬프트 매핑 설정 (OpenAI Playground에서 관리)
    CHATBOT_PROMPTS: Dict[str, Dict[str, str]] = {
        "opening": {
            "id": "pmpt_68c122b7fbc88196bdc8680f93b044860281f0ca8bc85937",
            "version": "20"
        },
        "dilemma": {
            "id": "pmpt_68c123df86948197a9be12f7344438270a5924971aab8f27", 
            "version": "15"
        },
        "flip": {
            "id": "pmpt_68c1294a9c788190a354084edf3e5b4e0551d09aeaea88c0",
            "version": "21"
        },
        "roles": {
            "id": "pmpt_68c12508f4088193905744bdf4a5aa4a0b87855a9b1545b0",
            "version": "15"
        },
        "ending": {
            "id": "pmpt_68c12982ae048190aaed3a4004918f1a09e33c363c985ff5",
            "version": "20"
        }
    }
    
    # 음성 처리 관련 설정
    AUDIO_UPLOAD_DIR: str = "static/audio"
    MAX_AUDIO_SIZE_MB: int = 10
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()