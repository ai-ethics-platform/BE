# LangChain을 활용한 구조화된 JSON 응답 파싱 구현기

## 📋 목차
1. [문제 상황](#문제-상황)
2. [해결 방안](#해결-방안)
3. [아키텍처 설계](#아키텍처-설계)
4. [구현 세부사항](#구현-세부사항)
5. [코드 구조](#코드-구조)
6. [동작 흐름](#동작-흐름)
7. [장단점 분석](#장단점-분석)
8. [결론](#결론)

---

## 문제 상황

### 기존 방식의 한계

다단계 챗봇 시스템을 구축하면서 다음과 같은 문제:

1. **프론트엔드 규칙 기반 파싱의 한계**
   - OpenAI Playground API로부터 받은 자유 형식 텍스트 응답에서 변수를 추출해야 함
   - 정규표현식이나 키워드 기반 파싱으로는 다양한 응답 형식에 대응하기 어려움
   - 응답 형식이 조금만 달라져도 파싱 실패

2. **다단계 대화 흐름 관리의 복잡성**
   - 각 단계(`opening` → `dilemma` → `flip` → `roles` → `ending`)마다 다음 단계로 전달할 변수가 다름
   - 예: `opening` 단계에서는 `topic` 변수를 추출해야 하고, `dilemma` 단계에서는 `question`, `choice1`, `choice2` 변수 필요
   - 프론트엔드에서 각 단계별로 다른 파싱 로직을 구현해야 하는 부담

3. **유지보수성 문제**
   - 프롬프트가 변경되면 파싱 로직도 함께 수정해야 함
   - 파싱 실패 시 디버깅이 어려움

### 예시: 기존 방식의 문제점

```python
# 프론트엔드에서 시도했던 방식
response_text = "AI 윤리에 대한 딜레마를 제시합니다. 주제: AI 윤리"

# 정규표현식으로 파싱 시도
import re
topic_match = re.search(r'주제:\s*(.+)', response_text)
topic = topic_match.group(1) if topic_match else None

# 문제: 응답 형식이 바뀌면 파싱 실패
# "주제는 AI 윤리입니다" → 파싱 실패
# "Topic: AI Ethics" → 파싱 실패
```

---

## 해결 방안

### LangChain + PydanticOutputParser 사용용

**핵심 아이디어**: LLM이 생성한 자유 형식 텍스트를 다시 LLM에게 구조화된 JSON으로 변환하도록 요청

**주요 기술 스택**:
- **LangChain**: LLM 체인 구성 및 출력 파싱
- **PydanticOutputParser**: Pydantic 모델을 기반으로 구조화된 출력 강제
- **Pydantic**: 타입 안전성과 검증을 위한 데이터 모델

### 왜 LangChain인가?

1. **구조화된 출력 보장**: `PydanticOutputParser`가 LLM 출력을 강제로 JSON 형식으로 변환
2. **타입 안전성**: Pydantic 모델로 스키마 정의 및 자동 검증
3. **유연한 체인 구성**: 프롬프트 → LLM → 파서를 파이프라인으로 구성
4. **에러 처리**: 파싱 실패 시 graceful fallback 가능

---

## 아키텍처 설계

### 전체 흐름도

```
┌─────────────────┐
│  OpenAI         │
│  Playground API │
└────────┬────────┘
         │
         │ 자유 형식 텍스트 응답
         ▼
┌─────────────────┐
│  Raw Response   │
│  Text           │
└────────┬────────┘
         │
         │ LangChain 파이프라인
         ▼
┌─────────────────────────────────┐
│  1. ChatPromptTemplate          │
│     - JSON 변환 지시            │
│     - Pydantic 스키마 설명      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  2. ChatOpenAI (gpt-4o-mini)    │
│     - 텍스트 → JSON 변환        │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  3. PydanticOutputParser        │
│     - JSON → Pydantic 모델      │
│     - 타입 검증                 │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Parsed Variables               │
│  {                              │
│    "response_text": "...",      │
│    "topic": "AI 윤리",          │
│    ...                          │
│  }                              │
└─────────────────────────────────┘
```

### 2단계 처리 방식

1. **1단계: OpenAI Playground API 호출**
   - 프롬프트 ID와 버전을 사용하여 프롬프트 처리
   - 자유 형식 텍스트 응답 받음

2. **2단계: LangChain으로 구조화**
   - 받은 텍스트를 LangChain 파이프라인에 입력
   - Pydantic 모델에 맞는 JSON으로 변환
   - 변수 추출 및 검증

---

## 구현 세부사항

### 1. Pydantic 모델 정의

각 단계별로 필요한 변수를 명시적으로 정의:

```python
# app/schemas/step_responses.py

from pydantic import BaseModel, Field
from typing import Optional

class OpeningResponse(BaseModel):
    """opening 단계 응답 모델 - topic 변수 추출 (dilemma 단계에 전달)"""
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    topic: Optional[str] = Field(None, description="다음 단계(dilemma)에 전달할 topic 변수")

class DilemmaResponse(BaseModel):
    """dilemma 단계 응답 모델 - question, choice1, choice2 변수 추출 (flip 단계에 전달)"""
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    question: Optional[str] = Field(None, description="다음 단계(flip)에 전달할 question 변수")
    choice1: Optional[str] = Field(None, description="다음 단계(flip)에 전달할 choice1 변수")
    choice2: Optional[str] = Field(None, description="다음 단계(flip)에 전달할 choice2 변수")

class FlipResponse(BaseModel):
    """flip 단계 응답 모델 - structure 변수 추출 (roles 단계에 전달)"""
    response_text: str = Field(..., description="사용자에게 보여줄 응답 텍스트")
    structure: Optional[str] = Field(None, description="다음 단계(roles)에 전달할 structure 변수")

# 단계별 응답 모델 매핑
STEP_RESPONSE_MODELS = {
    "opening": OpeningResponse,
    "dilemma": DilemmaResponse,
    "flip": FlipResponse,
    "roles": RolesResponse,
    "ending": EndingResponse,
}
```

**핵심 포인트**:
- `Field`의 `description`이 LLM에게 각 필드의 의미를 전달
- `Optional` 타입으로 파싱 실패 시에도 안전하게 처리
- 각 모델은 다음 단계에 필요한 변수만 포함

### 2. LangChain 파이프라인 구성

```python
# app/services/chat_service.py

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import PydanticOutputParser

async def call_openai_response(self, step: str, user_input: str, context: Dict[str, Any]):
    # 1. OpenAI Playground API 호출
    response = self.openai_client.responses.create(
        prompt={
            "id": prompt_config["id"],
            "version": prompt_config["version"]
        },
        input=user_input,
        input_variables=input_variables
    )
    
    raw_response_text = extract_text_from_response(response)
    
    # 2. LangChain으로 JSON 파싱
    parsed_variables = {}
    try:
        # 단계별 응답 모델 가져오기
        response_model = STEP_RESPONSE_MODELS.get(step)
        if response_model:
            # LLM 초기화
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                api_key=settings.OPENAI_API_KEY,
            )
            
            # PydanticOutputParser 생성
            parser = PydanticOutputParser(pydantic_object=response_model)
            
            # JSON 형식 지시사항 자동 생성
            format_instructions = parser.get_format_instructions()
            
            # 프롬프트 템플릿 구성
            prompt_template = ChatPromptTemplate.from_template(
                """다음 응답을 JSON 형식으로 변환해주세요. 
응답 텍스트: {raw_response}

{format_instructions}

원본 응답의 내용을 유지하면서, 위 JSON 스키마에 맞춰서 구조화해주세요.
response_text 필드에는 사용자에게 보여줄 원본 응답 텍스트를 넣어주세요."""
            )
            
            # 체인 실행 (프롬프트 → LLM → 파서)
            chain = prompt_template | llm | parser
            parsed_result = await chain.ainvoke({
                "raw_response": raw_response_text,
                "format_instructions": format_instructions
            })
            
            # 파싱된 결과에서 변수 추출
            if isinstance(parsed_result, BaseModel):
                parsed_dict = parsed_result.model_dump()
                # response_text는 제외하고 나머지를 variables로
                parsed_variables = {
                    k: v for k, v in parsed_dict.items() 
                    if k != "response_text"
                }
                
    except Exception as parse_error:
        # 파싱 실패 시 원본 텍스트 사용 (graceful fallback)
        pass
    
    return raw_response_text, parsed_variables
```

**핵심 포인트**:
- `PydanticOutputParser`가 자동으로 JSON 스키마 지시사항 생성
- `chain = prompt_template | llm | parser`로 파이프라인 구성
- 파싱 실패 시에도 원본 텍스트는 반환 (안정성)

### 3. 이미지 생성 API에도 적용

이미지 생성 프롬프트도 구조화하여 더 정확한 이미지 생성:

```python
# app/api/endpoints/chat.py

from app.schemas.chat import GeneratedImage

@router.post("/chat/image")
async def generate_image(payload: ImageRequest):
    # LangChain으로 이미지 생성 프롬프트 구조화
    prompt_template = ChatPromptTemplate.from_template(
        """You are an image generation assistant.
User input: {input}
Variables (context): {variables}

Return a JSON object describing the intended image:
{{
  "description": "detailed content of the image",
  "style": "art style or tone",
  "size": "image size",
  "reasoning": "brief reasoning why this fits the user's intent"
}}"""
    )
    
    parser = PydanticOutputParser(pydantic_object=GeneratedImage)
    chain = prompt_template | llm | parser
    
    parsed_result = await chain.ainvoke({
        "input": payload.input,
        "variables": variables
    })
    
    # 구조화된 description을 DALL-E 프롬프트로 사용
    final_prompt = parsed_result.description
    img = client.images.generate(
        model="dall-e-3",
        prompt=final_prompt,
        size=size,
    )
```

---

## 코드 구조

### 파일 구조

```
app/
├── schemas/
│   ├── step_responses.py      # 단계별 Pydantic 응답 모델
│   ├── chat_session.py         # API 요청/응답 스키마
│   └── chat.py                 # 이미지 생성 스키마
├── services/
│   └── chat_service.py         # LangChain 파이프라인 로직
└── api/
    └── endpoints/
        └── chat.py             # API 엔드포인트
```

### 주요 컴포넌트

1. **`STEP_RESPONSE_MODELS`**: 단계별 응답 모델 매핑
2. **`call_openai_response()`**: 2단계 처리 로직
3. **`PydanticOutputParser`**: JSON 파싱 및 검증
4. **`ChatPromptTemplate`**: JSON 변환 프롬프트

---

## 동작 흐름

### 전체 시퀀스 다이어그램

```
사용자 → API 요청
  │
  ▼
[1] OpenAI Playground API 호출
  │
  ├─→ 프롬프트 ID: pmpt_xxx
  ├─→ 버전: 20
  └─→ 사용자 입력 + 컨텍스트 변수
  │
  ▼
[2] 자유 형식 텍스트 응답 수신
  │
  ├─→ "안녕하세요! AI 윤리에 대해 이야기하고 싶으시군요. 
  │    주제는 AI 윤리입니다. 이는..."
  │
  ▼
[3] LangChain 파이프라인 실행
  │
  ├─→ ChatPromptTemplate
  │   └─→ "다음 응답을 JSON 형식으로 변환해주세요..."
  │
  ├─→ ChatOpenAI (gpt-4o-mini)
  │   └─→ JSON 형식으로 변환된 응답 생성
  │
  └─→ PydanticOutputParser
      └─→ Pydantic 모델로 파싱 및 검증
  │
  ▼
[4] 구조화된 변수 추출
  │
  ├─→ parsed_variables = {
  │     "topic": "AI 윤리"
  │   }
  │
  └─→ response_text = "안녕하세요! AI 윤리에 대해 이야기하고 싶으시군요..."
  │
  ▼
[5] 컨텍스트에 변수 저장
  │
  ├─→ context["opening_topic"] = "AI 윤리"
  │
  └─→ 다음 단계(dilemma)에서 사용
  │
  ▼
[6] API 응답 반환
  │
  └─→ {
       "response_text": "...",
       "parsed_variables": {"topic": "AI 윤리"},
       "current_step": "opening",
       "next_step": "dilemma"
     }
```

### 실제 예시

**입력 (opening 단계)**:
```json
{
  "session_id": "session-123",
  "user_input": "AI 윤리에 대해 이야기하고 싶어요",
  "step": "opening"
}
```

**1단계: OpenAI Playground API 응답**:
```
"안녕하세요! AI 윤리에 대해 이야기하고 싶으시군요. 
주제는 AI 윤리입니다. 이는 현대 사회에서 가장 중요한 
윤리적 고민 중 하나입니다..."
```

**2단계: LangChain 파싱 결과**:
```json
{
  "response_text": "안녕하세요! AI 윤리에 대해 이야기하고 싶으시군요...",
  "topic": "AI 윤리"
}
```

**최종 API 응답**:
```json
{
  "session_id": "session-123",
  "current_step": "opening",
  "response_text": "안녕하세요! AI 윤리에 대해 이야기하고 싶으시군요...",
  "parsed_variables": {
    "topic": "AI 윤리"
  },
  "context": {
    "opening_topic": "AI 윤리"
  },
  "next_step": "dilemma",
  "is_complete": false
}
```

**다음 단계 (dilemma)에서 topic 사용**:
- `context`에 `opening_topic`이 저장되어 있으므로 dilemma 프롬프트에서 `{{topic}}` 변수로 사용 가능

---

## 장단점 분석

### 장점 ✅

1. **높은 파싱 성공률**
   - LLM이 LLM 출력을 파싱하므로 다양한 형식에 대응 가능
   - 정규표현식보다 훨씬 유연함

2. **타입 안전성**
   - Pydantic 모델로 스키마 강제 및 자동 검증
   - 런타임 타입 체크

3. **유지보수성 향상**
   - 프롬프트 변경 시 파싱 로직 수정 불필요
   - Pydantic 모델만 수정하면 자동 반영

4. **Graceful Fallback**
   - 파싱 실패 시에도 원본 텍스트 반환
   - 서비스 중단 없이 안정적 운영

5. **명확한 스키마 정의**
   - 각 단계별 필요한 변수가 코드에 명시적으로 정의됨
   - 문서화 효과

### 단점 ❌

1. **추가 API 호출 비용**
   - OpenAI Playground API 호출 + LangChain LLM 호출
   - 비용이 2배로 증가 (하지만 gpt-4o-mini 사용으로 절감)

2. **응답 시간 증가**
   - 2단계 처리로 인한 지연 시간
   - 약 1-2초 추가 소요

3. **의존성 증가**
   - LangChain 라이브러리 추가
   - 설치 시간 증가 (의존성이 많음)

4. **복잡도 증가**
   - 코드 복잡도가 다소 증가
   - 디버깅 난이도 상승

### 비용 최적화

- **gpt-4o-mini 사용**: 파싱용으로는 저렴한 모델 사용
- **캐싱 고려**: 동일한 입력에 대해 파싱 결과 캐싱 가능
- **선택적 파싱**: 중요한 단계에서만 파싱 수행

---

## 에러 처리 및 안정성

### 파싱 실패 시나리오

```python
try:
    parsed_result = await chain.ainvoke({...})
except Exception as parse_error:
    # 파싱 실패 시 원본 텍스트 사용
    parsed_variables = {}
    # 로깅 (선택적)
    logger.warning(f"LangChain parsing failed: {parse_error}")
```

### 안정성 보장

1. **Try-Except 블록**: 파싱 실패해도 서비스 중단 없음
2. **Optional 타입**: Pydantic 필드가 Optional이므로 None 허용
3. **Fallback 메커니즘**: 파싱 실패 시 원본 텍스트 반환

---

## 실제 사용 사례

### 케이스 1: 다단계 챗봇

```python
# opening 단계에서 topic 추출
response = await chat_service.process_multi_step_chat(
    db, 
    MultiStepChatRequest(
        session_id="session-123",
        user_input="AI 윤리에 대해 이야기하고 싶어요",
        step="opening"
    )
)

# parsed_variables에서 topic 추출
topic = response.parsed_variables.get("topic")  # "AI 윤리"

# 다음 단계(dilemma)에서 topic 사용
# context에 opening_topic이 자동으로 저장되어 dilemma 프롬프트에서 사용 가능
next_response = await chat_service.process_multi_step_chat(
    db,
    MultiStepChatRequest(
        session_id="session-123",
        user_input="...",
        step="dilemma"
    )
)
# dilemma 단계에서는 question, choice1, choice2를 추출하여 flip에 전달
```

### 케이스 2: 이미지 생성

```python
# 사용자 입력을 구조화된 이미지 설명으로 변환
response = await generate_image(ImageRequest(
    input="AI 로봇과 사람이 대화하는 장면",
    context={"topic": "AI 윤리"}
))

# parsed_result에서 상세 정보 추출
description = response.parsed_result["description"]
style = response.parsed_result["style"]
reasoning = response.parsed_result["reasoning"]
```

## 참고 자료

- [LangChain 공식 문서](https://python.langchain.com/)
- [Pydantic 공식 문서](https://docs.pydantic.dev/)
- [OpenAI Playground API](https://platform.openai.com/docs/guides/prompt-engineering)


