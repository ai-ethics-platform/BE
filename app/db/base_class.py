from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    id: Any
    __name__: str
    
    # 클래스 이름을 소문자로 변환하여 테이블 이름으로 사용
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() 