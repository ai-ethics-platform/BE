from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field


# 각 단계별 응답 모델 정의 (JSON 구조화된 출력)
# 다음 단계로 넘어가기 위해 필요한 변수들을 명시적으로 정의

class OpeningResponse(BaseModel):
    """opening 단계 응답 모델 - topic 변수 추출 (question 단계에 전달)"""
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    topic: Optional[str] = Field(None, description="다음 단계(question)에 전달할 topic 변수")
    # opening → question: topic 필요


class QuestionResponse(BaseModel):
    """question 단계 응답 모델 - question, choice1, choice2 변수 추출 (flip 단계에 전달)"""
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    question: Optional[str] = Field(None, description="다음 단계(flip)에 전달할 question 변수")
    choice1: Optional[str] = Field(None, description="다음 단계(flip)에 전달할 choice1 변수")
    choice2: Optional[str] = Field(None, description="다음 단계(flip)에 전달할 choice2 변수")
    # question → flip: question, choice1, choice2 필요


class FlipResponse(BaseModel):
    """flip 단계 응답 모델 - 시나리오와 플립 상황 변수 추출 (roles 단계에 전달)"""
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    dilemma_situation: Optional[str] = Field(None, description="상황 시나리오")
    question: Optional[str] = Field(None, description="딜레마 질문")
    choice1: Optional[str] = Field(None, description="선택지 1 (agree_label)")
    flips_agree_texts: Optional[str] = Field(None, description="선택지 1에 대한 플립 자료")
    choice2: Optional[str] = Field(None, description="선택지 2 (disagree_label)")
    flips_disagree_texts: Optional[str] = Field(None, description="선택지 2에 대한 플립 자료")
    # flip → roles: 모든 플립 자료 전달


class RolesResponse(BaseModel):
    """roles 단계 응답 모델 - 역할 캐릭터 변수 추출 (ending 단계에 전달)"""
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    char1: Optional[str] = Field(None, description="역할 1 이름")
    chardes1: Optional[str] = Field(None, description="역할 1 배경 설명")
    char2: Optional[str] = Field(None, description="역할 2 이름")
    chardes2: Optional[str] = Field(None, description="역할 2 배경 설명")
    char3: Optional[str] = Field(None, description="역할 3 이름")
    chardes3: Optional[str] = Field(None, description="역할 3 배경 설명")
    # roles → ending: 역할 자료 전달


class EndingResponse(BaseModel):
    """ending 단계 응답 모델 - 최종 템플릿 완성

    ending 프롬프트(v24)의 [확정 단계] 포맷은 섹션 마커(🎬/🎭/🎯/✅/🌀)가
    고정되어 있다. 추출기(gpt-4o-mini)가 어느 텍스트를 어느 필드에 넣을지
    헤매지 않도록 description에 마커 위치를 명시한다. (QA #13 — 이 필드들이
    비면 프론트의 '템플릿 생성' 버튼이 나타나지 않는다)
    """
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    opening: Optional[List[str]] = Field(None, description="오프닝 멘트 (문장 배열). '🎬 오프닝 멘트' 섹션 아래 문단의 문장들")
    char1: Optional[str] = Field(None, description="역할 1 이름. '🎭 역할' 섹션 첫 번째 항목의 이름")
    chardes1: Optional[str] = Field(None, description="역할 1 배경 설명. '🎭 역할' 섹션 첫 번째 항목의 설명")
    char2: Optional[str] = Field(None, description="역할 2 이름. '🎭 역할' 섹션 두 번째 항목의 이름")
    chardes2: Optional[str] = Field(None, description="역할 2 배경 설명. '🎭 역할' 섹션 두 번째 항목의 설명")
    char3: Optional[str] = Field(None, description="역할 3 이름. '🎭 역할' 섹션 세 번째 항목의 이름")
    chardes3: Optional[str] = Field(None, description="역할 3 배경 설명. '🎭 역할' 섹션 세 번째 항목의 설명")
    dilemma_situation: Optional[List[str]] = Field(None, description="상황 시나리오 (문장 배열). '🎯 상황 및 딜레마 질문' 섹션에서 '질문:' 이전까지의 문장들")
    question: Optional[str] = Field(None, description="딜레마 질문. '🎯' 섹션 안 '질문:' 뒤의 한 문장")
    agree_label: Optional[str] = Field(None, description="선택지 1 라벨. '✅ 선택지 1:' 뒤의 텍스트")
    disagree_label: Optional[str] = Field(None, description="선택지 2 라벨. '✅ 선택지 2:' 뒤의 텍스트")
    flips_agree_texts: Optional[List[str]] = Field(None, description="선택지 1 플립 자료 (문장 배열). '✅ 선택지 1' 아래 '플립자료:' 뒤의 문장들")
    flips_disagree_texts: Optional[List[str]] = Field(None, description="선택지 2 플립 자료 (문장 배열). '✅ 선택지 2' 아래 '플립자료:' 뒤의 문장들")
    agreeEnding: Optional[str] = Field(None, description="선택지 1 최종 멘트. '🌀 최종 멘트' 섹션에서 '-- 선택지1 최종선택:' 뒤의 문장")
    disagreeEnding: Optional[str] = Field(None, description="선택지 2 최종 멘트. '🌀 최종 멘트' 섹션에서 '-- 선택지2 최종선택:' 뒤의 문장")
    # ending: 마지막 단계 - 모든 정보 취합


# 단계별 응답 모델 매핑
STEP_RESPONSE_MODELS = {
    "opening": OpeningResponse,
    "question": QuestionResponse,
    "flip": FlipResponse,
    "roles": RolesResponse,
    "ending": EndingResponse,
}

