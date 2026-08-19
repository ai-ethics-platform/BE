from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field


# 각 단계별 응답 모델 정의 (JSON 구조화된 출력)
# 다음 단계로 넘어가기 위해 필요한 변수들을 명시적으로 정의

class OpeningResponse(BaseModel):
    """opening 단계 응답 모델 - topic 변수 추출 (question 단계에 전달)"""
    response_text: Optional[str] = Field(default="", description="사용자에게 보여줄 응답 텍스트(추출하지 않음)")
    topic: Optional[str] = Field(None, description="다음 단계(question)에 전달할 topic 변수")
    # opening → question: topic 필요


class QuestionResponse(BaseModel):
    """question 단계 응답 모델 - question, choice1, choice2 변수 추출 (flip 단계에 전달)

    질문/선택지는 반드시 '- 질문:' '- 선택지1:' '- 선택지2:' 마커 뒤의 텍스트에서만
    추출한다. 마커가 없는 텍스트(인사말, 가치 충돌 설명 등)에서 값을 추측해 채우면
    세션에 저장된 정상 값을 덮어쓰게 된다. (QA 8/17 #3)
    """
    response_text: Optional[str] = Field(default="", description="사용자에게 보여줄 응답 텍스트(추출하지 않음)")
    question: Optional[str] = Field(None, description="다음 단계(flip)에 전달할 question 변수. '- 질문:' 마커 뒤의 텍스트에서만 추출하고, 마커가 없으면 null")
    choice1: Optional[str] = Field(None, description="다음 단계(flip)에 전달할 choice1 변수. '- 선택지1:' 마커 뒤의 텍스트에서만 추출하고, 마커가 없으면 null")
    choice2: Optional[str] = Field(None, description="다음 단계(flip)에 전달할 choice2 변수. '- 선택지2:' 마커 뒤의 텍스트에서만 추출하고, 마커가 없으면 null")
    # question → flip: question, choice1, choice2 필요


class FlipResponse(BaseModel):
    """flip 단계 응답 모델 - 시나리오와 플립 상황 변수 추출 (roles 단계에 전달)

    각 필드는 반드시 해당 마커 뒤의 텍스트에서만 추출한다. 마커가 없는 텍스트
    (단계 진입 인사말, 자유 대화 등)에서 값을 추측해 채우면 세션에 저장된 정상 값을
    덮어쓰게 된다. (QA 8/17 #3 — 인사말의 "두 가지 선택지 중 하나를 고릅니다"가
    choice1로 잘못 추출된 사례)
    """
    response_text: Optional[str] = Field(default="", description="사용자에게 보여줄 응답 텍스트(추출하지 않음)")
    dilemma_situation: Optional[str] = Field(None, description="상황 시나리오. '- 상황 시나리오:' 마커 뒤의 텍스트에서만 추출하고, 마커가 없으면 null")
    question: Optional[str] = Field(None, description="딜레마 질문. '- 질문:' 마커 뒤의 텍스트에서만 추출하고, 마커가 없으면 null")
    choice1: Optional[str] = Field(None, description="선택지 1 (agree_label). '- 선택지1:' 마커 뒤의 텍스트에서만 추출하고, 마커가 없으면 null")
    flips_agree_texts: Optional[str] = Field(None, description="선택지 1에 대한 결과 자료. '- 선택지1:' 줄 다음에 오는 '플립자료:' 또는 '예상하지 못한 결과:' 라벨 뒤의 텍스트에서만 추출하고, 라벨이 없으면 null")
    choice2: Optional[str] = Field(None, description="선택지 2 (disagree_label). '- 선택지2:' 마커 뒤의 텍스트에서만 추출하고, 마커가 없으면 null")
    flips_disagree_texts: Optional[str] = Field(None, description="선택지 2에 대한 결과 자료. '- 선택지2:' 줄 다음에 오는 '플립자료:' 또는 '예상하지 못한 결과:' 라벨 뒤의 텍스트에서만 추출하고, 라벨이 없으면 null")
    # flip → roles: 모든 플립 자료 전달


class RolesResponse(BaseModel):
    """roles 단계 응답 모델 - 역할 캐릭터 변수 추출 (ending 단계에 전달)"""
    response_text: Optional[str] = Field(default="", description="사용자에게 보여줄 응답 텍스트(추출하지 않음)")
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

    마커는 볼드(**)로 감싸져 나올 수 있고, '선택지 1'/'최종 선택'처럼
    띄어쓰기가 들어갈 수 있다. 어느 쪽이든 같은 필드로 취급한다. (QA #13, #18)
    """
    response_text: Optional[str] = Field(default="", description="사용자에게 보여줄 응답 텍스트(추출하지 않음)")
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
    flips_agree_texts: Optional[List[str]] = Field(None, description="선택지 1 결과 자료 (문장 배열). '✅ 선택지 1' 아래 '예상하지 못한 결과:' 또는 (구버전) '플립자료:' 뒤의 문장들")
    flips_disagree_texts: Optional[List[str]] = Field(None, description="선택지 2 결과 자료 (문장 배열). '✅ 선택지 2' 아래 '예상하지 못한 결과:' 또는 (구버전) '플립자료:' 뒤의 문장들")
    agreeEnding: Optional[str] = Field(None, description="선택지 1 최종 멘트. '🌀 최종 멘트' 섹션에서 '-- 선택지1 최종선택:' 뒤의 문장. '선택지 1', '최종 선택'처럼 띄어쓴 표기도 같은 항목이다")
    disagreeEnding: Optional[str] = Field(None, description="선택지 2 최종 멘트. '🌀 최종 멘트' 섹션에서 '-- 선택지2 최종선택:' 뒤의 문장. '선택지 2', '최종 선택'처럼 띄어쓴 표기도 같은 항목이다")
    # ending: 마지막 단계 - 모든 정보 취합


# 단계별 응답 모델 매핑
STEP_RESPONSE_MODELS = {
    "opening": OpeningResponse,
    "question": QuestionResponse,
    "flip": FlipResponse,
    "roles": RolesResponse,
    "ending": EndingResponse,
}

