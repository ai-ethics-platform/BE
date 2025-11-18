from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field


# 각 단계별 응답 모델 정의 (JSON 구조화된 출력)
# 다음 단계로 넘어가기 위해 필요한 변수들을 명시적으로 정의

class OpeningResponse(BaseModel):
    """opening 단계 응답 모델 - 변수 불필요"""
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    # opening → dilemma: 변수 불필요


class DilemmaResponse(BaseModel):
    """dilemma 단계 응답 모델 - topic 변수 필요"""
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    topic: Optional[str] = Field(None, description="다음 단계(flip)에 전달할 topic 변수")
    # dilemma → flip: topic 필요


class FlipResponse(BaseModel):
    """flip 단계 응답 모델 - question, choice1, choice2 변수 필요"""
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    question: Optional[str] = Field(None, description="다음 단계(roles)에 전달할 question 변수")
    choice1: Optional[str] = Field(None, description="다음 단계(roles)에 전달할 choice1 변수")
    choice2: Optional[str] = Field(None, description="다음 단계(roles)에 전달할 choice2 변수")
    # flip → roles: question, choice1, choice2 필요


class RolesResponse(BaseModel):
    """roles 단계 응답 모델 - structure 변수 필요"""
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    structure: Optional[str] = Field(None, description="다음 단계(ending)에 전달할 structure 변수")
    # roles → ending: structure 필요


class EndingResponse(BaseModel):
    """ending 단계 응답 모델 - structure, role 변수 필요"""
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    structure: Optional[str] = Field(None, description="ending 단계에 필요한 structure 변수")
    role: Optional[str] = Field(None, description="ending 단계에 필요한 role 변수")
    # ending: 마지막 단계이므로 다음 단계 없음


# 단계별 응답 모델 매핑
STEP_RESPONSE_MODELS = {
    "opening": OpeningResponse,
    "dilemma": DilemmaResponse,
    "flip": FlipResponse,
    "roles": RolesResponse,
    "ending": EndingResponse,
}

