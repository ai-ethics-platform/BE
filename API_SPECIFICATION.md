# AI 윤리 챗봇 API 명세서

## 📋 목차
1. [개요](#개요)
2. [다단계 챗봇 API](#다단계-챗봇-api)
3. [단계별 상세 가이드](#단계별-상세-가이드)
4. [이미지 생성 API](#이미지-생성-api)
5. [세션 관리 API](#세션-관리-api)
6. [에러 처리](#에러-처리)

---

## 개요

AI 윤리 토론을 위한 다단계 챗봇 시스템 API입니다. 

**주요 기술:**
- **LangChain**: 구조화된 JSON 응답 파싱
- **OpenAI Playground**: 프롬프트 관리
- **Pydantic**: 타입 안전성 및 검증

**Base URL**: `https://dilemmai.org`

---

## 다단계 챗봇 API

### `POST /chat/multi-step`

다단계 대화를 진행하며, 각 단계에서 LangChain으로 구조화된 변수를 추출합니다.

---

### 🔄 단계 순서

```
opening → dilemma → flip → roles → ending
```

| 단계 | 설명 | 추출 변수 | 다음 단계에 전달 |
|------|------|-----------|-----------------|
| **opening** | 주제 선택 | `topic` | dilemma에 전달 |
| **dilemma** | 딜레마 생성 | `question`, `choice1`, `choice2` | flip에 전달 |
| **flip** | 반대 입장 제시 | `structure` | roles에 전달 |
| **roles** | 역할 분배 | `structure`, `role` | ending에 전달 |
| **ending** | 마무리 | - | 완료 |

---

### 📤 Request Schema

```json
{
  "session_id": "unique-session-id",
  "user_input": "사용자 입력 텍스트",
  "step": "opening"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `session_id` | string | ✅ | 세션 식별자 (전체 대화 추적용) |
| `user_input` | string | ✅ | 사용자 입력 텍스트 |
| `step` | string | ❌ | 특정 단계로 강제 이동 (보통 생략) |

**주의사항:**
- `step`을 생략하면 자동으로 다음 단계로 진행됩니다
- 첫 요청에서만 `step: "opening"` 명시 권장
- 동일한 `session_id`를 모든 단계에서 사용해야 합니다

---

### 📥 Response Schema

```json
{
  "session_id": "unique-session-id",
  "current_step": "opening",
  "response_text": "사용자에게 보여줄 응답 텍스트",
  "parsed_variables": {
    "topic": "AI 윤리"
  },
  "context": {
    "opening_result": "...",
    "opening_user_input": "...",
    "opening_topic": "AI 윤리"
  },
  "next_step": "dilemma",
  "is_complete": false
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `session_id` | string | 세션 식별자 |
| `current_step` | string | 현재 실행된 단계 |
| `response_text` | string | 사용자에게 보여줄 응답 텍스트 |
| `parsed_variables` | object \| {} | LangChain으로 추출된 구조화된 변수 (파싱 실패 시 빈 객체) |
| `context` | object | 전체 대화 컨텍스트 (모든 이전 단계의 결과 포함) |
| `next_step` | string \| null | 다음 단계 이름 (마지막 단계면 null) |
| `is_complete` | boolean | 대화 완료 여부 (ending 단계에서 true) |

---

### 🔧 변수 매핑 구조

백엔드는 **context 저장**과 **OpenAI 프롬프트 전달** 시 변수 이름을 매핑합니다:

```python
{
  "opening": {},  # 변수 불필요
  
  "dilemma": {
    "opening_topic": "topic"  # context의 opening_topic → 프롬프트의 topic
  },
  
  "flip": {
    "dilemma_question": "question",
    "dilemma_choice1": "choice1",
    "dilemma_choice2": "choice2"
  },
  
  "roles": {
    "flip_structure": "structure"
  },
  
  "ending": {
    "roles_structure": "structure",
    "roles_role": "role"
  }
}
```

**왜 매핑이 필요한가?**
- **Context 저장**: 단계별 구분을 위해 `{step}_{variable}` 형식 사용 (예: `opening_topic`)
- **OpenAI 프롬프트**: 간단한 변수 이름 사용 (예: `topic`)
- 백엔드가 자동으로 변환하므로 프론트엔드는 신경 쓸 필요 없음

---

## 단계별 상세 가이드

### 1️⃣ Opening 단계 - 주제 선택

#### Request
```json
POST /chat/multi-step

{
  "session_id": "session-abc123",
  "user_input": "AI 윤리에 대해 이야기하고 싶어요",
  "step": "opening"
}
```

#### Response
```json
{
  "session_id": "session-abc123",
  "current_step": "opening",
  "response_text": "당신이 선택하신 주제는 AI 윤리입니다. AI 윤리는 인공지능 기술이 사회에 미치는 심리적, 사회적, 정치적 영향을 고려하는 분야입니다. 이대로 확정해도 괜찮은지, 다른 주제도 둘러보고 싶은지 확인해보고 수정할 부분이 있다면 알려주세요. (이대로 확정하고 넘어가고 싶다면 '다음 단계'를 입력해주세요.)",
  "parsed_variables": {
    "topic": "AI 윤리"
  },
  "context": {
    "opening_result": "당신이 선택하신 주제는 AI 윤리입니다...",
    "opening_user_input": "AI 윤리에 대해 이야기하고 싶어요",
    "opening_topic": "AI 윤리"
  },
  "next_step": "dilemma",
  "is_complete": false
}
```

#### 추출되는 변수
| 변수 | 설명 | 다음 단계 사용 |
|------|------|---------------|
| `topic` | 사용자가 선택한 AI 주제 | dilemma 프롬프트의 `{{topic}}` 변수로 전달 |

#### Context 저장
- `opening_result`: 원본 응답 텍스트
- `opening_user_input`: 사용자 입력
- `opening_topic`: 추출된 주제 (다음 단계에서 사용)

#### 프론트엔드 처리
```javascript
const response = await fetch('/chat/multi-step', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    user_input: userInput,
    step: 'opening'
  })
});

const data = await response.json();

// 1. 응답 텍스트 표시
displayMessage(data.response_text);

// 2. 추출된 주제 표시
if (data.parsed_variables?.topic) {
  displayTopicBadge(data.parsed_variables.topic);
}

// 3. 다음 단계 버튼 활성화
if (data.next_step === 'dilemma') {
  enableNextButton('딜레마 생성하기');
}
```

---

### 2️⃣ Dilemma 단계 - 딜레마 생성

#### Request
```json
POST /chat/multi-step

{
  "session_id": "session-abc123",
  "user_input": "자율주행차의 윤리적 딜레마를 만들어주세요"
}
```

**주의**: `step`을 생략하면 자동으로 다음 단계(dilemma)로 진행

#### Response
```json
{
  "session_id": "session-abc123",
  "current_step": "dilemma",
  "response_text": "자율주행차 딜레마: 사고 상황에서 탑승자와 보행자 중 누구를 우선해야 할까요?\n\n선택지 1: 탑승자의 안전을 최우선으로 보호\n선택지 2: 보행자의 안전을 최우선으로 보호",
  "parsed_variables": {
    "question": "사고 상황에서 탑승자와 보행자 중 누구를 우선해야 할까요?",
    "choice1": "탑승자의 안전을 최우선으로 보호",
    "choice2": "보행자의 안전을 최우선으로 보호"
  },
  "context": {
    "opening_topic": "AI 윤리",
    "opening_result": "...",
    "opening_user_input": "...",
    "dilemma_result": "자율주행차 딜레마: 사고 상황에서...",
    "dilemma_user_input": "자율주행차의 윤리적 딜레마를 만들어주세요",
    "dilemma_question": "사고 상황에서 탑승자와 보행자 중 누구를 우선해야 할까요?",
    "dilemma_choice1": "탑승자의 안전을 최우선으로 보호",
    "dilemma_choice2": "보행자의 안전을 최우선으로 보호"
  },
  "next_step": "flip",
  "is_complete": false
}
```

#### 이 단계에서 사용되는 변수
OpenAI Playground의 dilemma 프롬프트는 다음 변수를 받습니다:
- `topic`: opening 단계에서 추출된 주제 (context의 `opening_topic`에서 매핑됨)

#### 추출되는 변수
| 변수 | 설명 | 다음 단계 사용 |
|------|------|---------------|
| `question` | 생성된 딜레마 질문 | flip 프롬프트의 `{{question}}` 변수로 전달 |
| `choice1` | 첫 번째 선택지 | flip 프롬프트의 `{{choice1}}` 변수로 전달 |
| `choice2` | 두 번째 선택지 | flip 프롬프트의 `{{choice2}}` 변수로 전달 |

#### Context 저장
- `dilemma_result`: 원본 응답 텍스트
- `dilemma_user_input`: 사용자 입력
- `dilemma_question`: 추출된 질문
- `dilemma_choice1`: 첫 번째 선택지
- `dilemma_choice2`: 두 번째 선택지

#### 프론트엔드 처리
```javascript
const data = await response.json();

// 1. 딜레마 질문 표시
if (data.parsed_variables?.question) {
  displayDilemmaQuestion(data.parsed_variables.question);
}

// 2. 선택지 버튼 표시
if (data.parsed_variables?.choice1 && data.parsed_variables?.choice2) {
  displayChoiceButtons([
    {
      id: 'choice1',
      text: data.parsed_variables.choice1,
      onClick: () => selectChoice('choice1')
    },
    {
      id: 'choice2',
      text: data.parsed_variables.choice2,
      onClick: () => selectChoice('choice2')
    }
  ]);
}

// 3. 사용자가 선택지를 클릭하면 flip 단계로 이동
function selectChoice(choiceId) {
  const choiceText = data.parsed_variables[choiceId];
  sendToNextStep(`${choiceText}를 선택합니다`);
}
```

#### parsed_variables가 비어있는 경우
```json
{
  "parsed_variables": {}
}
```

**원인**: OpenAI Playground의 dilemma 프롬프트가 딜레마를 직접 생성하지 않고 추가 입력을 요구하는 경우

**해결 방법**:
1. OpenAI Playground의 dilemma 프롬프트를 수정하여 바로 딜레마 생성하도록 변경
2. 또는 `response_text`만 사용하여 사용자에게 표시

---

### 3️⃣ Flip 단계 - 반대 입장 제시

#### Request
```json
POST /chat/multi-step

{
  "session_id": "session-abc123",
  "user_input": "탑승자의 안전을 최우선으로 보호를 선택합니다"
}
```

#### Response
```json
{
  "session_id": "session-abc123",
  "current_step": "flip",
  "response_text": "탑승자 보호를 선택하셨군요. 하지만 반대 입장에서 생각해보면, 보행자도 도로를 안전하게 이용할 권리가 있습니다...",
  "parsed_variables": {
    "structure": "자동차 제조사, 보행자, 탑승자 3자 토론 구조"
  },
  "context": {
    "opening_topic": "AI 윤리",
    "dilemma_question": "...",
    "dilemma_choice1": "...",
    "dilemma_choice2": "...",
    "flip_result": "탑승자 보호를 선택하셨군요...",
    "flip_user_input": "탑승자의 안전을 최우선으로 보호를 선택합니다",
    "flip_structure": "자동차 제조사, 보행자, 탑승자 3자 토론 구조"
  },
  "next_step": "roles",
  "is_complete": false
}
```

#### 이 단계에서 사용되는 변수
OpenAI Playground의 flip 프롬프트는 다음 변수를 받습니다:
- `question`: dilemma 단계에서 추출된 질문 (context의 `dilemma_question`에서 매핑됨)
- `choice1`: dilemma 단계의 첫 번째 선택지
- `choice2`: dilemma 단계의 두 번째 선택지

#### 추출되는 변수
| 변수 | 설명 | 다음 단계 사용 |
|------|------|---------------|
| `structure` | 토론 구조 정보 | roles 프롬프트의 `{{structure}}` 변수로 전달 |

#### 프론트엔드 처리
```javascript
const data = await response.json();

// 1. 반대 입장 텍스트 표시
displayMessage(data.response_text);

// 2. 토론 구조 표시 (optional)
if (data.parsed_variables?.structure) {
  displayStructureInfo(data.parsed_variables.structure);
}

// 3. "역할 분배" 버튼
enableNextButton('역할 분배하기');
```

---

### 4️⃣ Roles 단계 - 역할 분배

#### Request
```json
POST /chat/multi-step

{
  "session_id": "session-abc123",
  "user_input": "역할을 분배해주세요"
}
```

#### Response
```json
{
  "session_id": "session-abc123",
  "current_step": "roles",
  "response_text": "다음과 같이 역할을 분배합니다:\n\n역할 1: 자동차 제조사 - 기술 개발자의 입장\n역할 2: 보행자 - 안전을 우선시하는 입장\n역할 3: 탑승자 - 개인의 권리를 중시하는 입장",
  "parsed_variables": {
    "structure": "3자 토론 구조",
    "role": "자동차 제조사, 보행자, 탑승자"
  },
  "context": {
    "flip_structure": "...",
    "roles_result": "다음과 같이 역할을 분배합니다...",
    "roles_user_input": "역할을 분배해주세요",
    "roles_structure": "3자 토론 구조",
    "roles_role": "자동차 제조사, 보행자, 탑승자"
  },
  "next_step": "ending",
  "is_complete": false
}
```

#### 이 단계에서 사용되는 변수
OpenAI Playground의 roles 프롬프트는 다음 변수를 받습니다:
- `structure`: flip 단계에서 추출된 토론 구조 (context의 `flip_structure`에서 매핑됨)

#### 추출되는 변수
| 변수 | 설명 | 다음 단계 사용 |
|------|------|---------------|
| `structure` | 토론 구조 정보 | ending 프롬프트의 `{{structure}}` 변수로 전달 |
| `role` | 할당된 역할들 | ending 프롬프트의 `{{role}}` 변수로 전달 |

#### 프론트엔드 처리
```javascript
const data = await response.json();

// 1. 역할 표시
if (data.parsed_variables?.role) {
  const roles = data.parsed_variables.role.split(', ');
  displayRoleCards(roles.map((role, index) => ({
    roleNumber: index + 1,
    roleName: role,
    assignedStudents: []
  })));
}

// 2. "마무리" 버튼
enableNextButton('마무리하기');
```

---

### 5️⃣ Ending 단계 - 마무리

#### Request
```json
POST /chat/multi-step

{
  "session_id": "session-abc123",
  "user_input": "마무리해주세요"
}
```

#### Response
```json
{
  "session_id": "session-abc123",
  "current_step": "ending",
  "response_text": "🎉 수고하셨습니다! 다음과 같은 AI 윤리 딜레마가 완성되었습니다:\n\n주제: AI 윤리\n질문: 사고 상황에서 탑승자와 보행자 중 누구를 우선해야 할까요?\n선택지 1: 탑승자의 안전을 최우선으로 보호\n선택지 2: 보행자의 안전을 최우선으로 보호\n\n역할: 자동차 제조사, 보행자, 탑승자\n\n이제 학생들과 함께 토론을 시작해보세요!",
  "parsed_variables": {},
  "context": {
    "opening_topic": "AI 윤리",
    "dilemma_question": "...",
    "dilemma_choice1": "...",
    "dilemma_choice2": "...",
    "roles_structure": "...",
    "roles_role": "...",
    "ending_result": "🎉 수고하셨습니다!...",
    "ending_user_input": "마무리해주세요"
  },
  "next_step": null,
  "is_complete": true
}
```

#### 이 단계에서 사용되는 변수
OpenAI Playground의 ending 프롬프트는 다음 변수를 받습니다:
- `structure`: roles 단계에서 추출된 구조 (context의 `roles_structure`에서 매핑됨)
- `role`: roles 단계에서 추출된 역할들 (context의 `roles_role`에서 매핑됨)

#### 추출되는 변수
없음 (마지막 단계이므로 다음 단계에 전달할 변수 불필요)

#### 프론트엔드 처리
```javascript
const data = await response.json();

// 1. 마무리 메시지 표시
displayMessage(data.response_text);

// 2. 완료 확인
if (data.is_complete) {
  // 전체 요약 표시
  displaySummary({
    topic: data.context.opening_topic,
    question: data.context.dilemma_question,
    choices: [
      data.context.dilemma_choice1,
      data.context.dilemma_choice2
    ],
    roles: data.context.roles_role
  });
  
  // 완료 화면
  showCompletionScreen();
  
  // "새 게임 시작" 버튼
  enableNewGameButton();
}
```

---

## 이미지 생성 API

### `POST /chat/image`

LangChain으로 이미지 생성 프롬프트를 구조화하고 DALL-E로 이미지를 생성합니다.

### Request
```json
{
  "input": "AI 로봇이 사람과 대화하는 장면",
  "step": "image",
  "context": {
    "topic": "AI 윤리",
    "style": "realistic"
  },
  "size": "1024x1024"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `input` | string | ✅ | 이미지 생성 프롬프트 텍스트 |
| `step` | string | ❌ | 단계 식별자 (기본값: "image") |
| `context` | object | ❌ | 컨텍스트 변수들 |
| `size` | string | ❌ | 이미지 크기 (기본값: "1024x1024") |

### Response
```json
{
  "step": "image",
  "image_data_url": "/static/generated_images/dalle_20240101_120000_abc123.png",
  "model": "dall-e-3",
  "size": "1024x1024",
  "parsed_result": {
    "description": "A detailed image showing an AI robot engaged in conversation with a human",
    "style": "realistic",
    "size": "1024x1024",
    "reasoning": "This image fits the user's intent because it depicts the ethical interaction between AI and humans"
  }
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `step` | string | 단계 식별자 |
| `image_data_url` | string | 생성된 이미지 URL (로컬 저장) |
| `model` | string | 사용된 모델 (항상 "dall-e-3") |
| `size` | string | 이미지 크기 |
| `parsed_result` | object \| null | LangChain으로 구조화된 이미지 정보 (파싱 실패 시 null) |

---

## 세션 관리 API

### 세션 정보 조회

#### `GET /chat/session/{session_id}`

```json
{
  "session_id": "session-abc123",
  "current_step": "dilemma",
  "context": {
    "opening_topic": "AI 윤리",
    "opening_result": "...",
    "dilemma_question": "...",
    ...
  },
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:30:00"
}
```

### 세션 삭제

#### `DELETE /chat/session/{session_id}`

```json
{
  "message": "Session session-abc123 deleted successfully"
}
```

---

## 에러 처리

### 에러 응답 형식

```json
{
  "detail": "에러 메시지"
}
```

### HTTP 상태 코드

| 코드 | 의미 | 예시 |
|------|------|------|
| `200` | 성공 | 정상 응답 |
| `400` | Bad Request | 잘못된 요청 파라미터 |
| `401` | Unauthorized | 인증 실패 |
| `404` | Not Found | 세션을 찾을 수 없음 |
| `500` | Internal Server Error | 서버 내부 오류 |
| `502` | Bad Gateway | OpenAI API 오류 |

### 일반적인 에러 예시

#### 1. OpenAI API 호출 실패
```json
{
  "detail": "OpenAI API call failed: Error code: 400 - {'error': {'message': 'Unknown prompt variables: ...'}}"
}
```

**원인**: OpenAI Playground 프롬프트에 정의되지 않은 변수 전달

**해결**: OpenAI Playground에서 해당 프롬프트의 Variables 섹션에 변수 정의

#### 2. LangChain 파싱 실패
파싱 실패 시 에러를 발생시키지 않고 `parsed_variables: {}`로 반환합니다.

```json
{
  "parsed_variables": {},
  "response_text": "원본 응답 텍스트"
}
```

**원인**: LLM이 JSON을 생성하지 못했거나 형식이 잘못됨

**해결**: `response_text`를 사용하여 사용자에게 표시

#### 3. 세션을 찾을 수 없음
```json
{
  "detail": "Session not-found-session-id not found"
}
```

**원인**: 존재하지 않는 session_id로 업데이트 시도

**해결**: 새로운 session_id로 opening 단계부터 시작

---

## 주의사항 및 베스트 프랙티스

### 1. 세션 관리

✅ **권장사항:**
```javascript
// 세션 ID 생성
const sessionId = `session-${Date.now()}-${Math.random().toString(36).substring(7)}`;

// 전체 대화 동안 동일한 ID 사용
localStorage.setItem('currentSessionId', sessionId);
```

❌ **피해야 할 것:**
- 각 요청마다 새로운 session_id 생성
- session_id 없이 요청

### 2. parsed_variables 처리

✅ **권장사항:**
```javascript
// parsed_variables가 비어있을 수 있으므로 항상 체크
if (data.parsed_variables && Object.keys(data.parsed_variables).length > 0) {
  // 구조화된 데이터 사용
  displayStructuredData(data.parsed_variables);
} else {
  // 원본 텍스트 사용
  displayRawText(data.response_text);
}
```

❌ **피해야 할 것:**
- `parsed_variables`가 항상 있다고 가정
- 빈 객체 체크 없이 바로 사용

### 3. step 파라미터 사용

✅ **권장사항:**
```javascript
// 첫 요청에서만 step 명시
const firstRequest = {
  session_id: sessionId,
  user_input: userInput,
  step: 'opening'
};

// 이후 요청에서는 생략 (자동 진행)
const nextRequest = {
  session_id: sessionId,
  user_input: userInput
  // step 생략
};
```

❌ **피해야 할 것:**
- 매번 step을 명시 (순서가 꼬일 수 있음)
- 임의로 단계 건너뛰기

### 4. 에러 처리

✅ **권장사항:**
```javascript
try {
  const response = await fetch('/chat/multi-step', {...});
  const data = await response.json();
  
  if (!response.ok) {
    // HTTP 에러 처리
    showError(data.detail || 'An error occurred');
    return;
  }
  
  // 정상 처리
  processResponse(data);
} catch (error) {
  // 네트워크 에러 처리
  showError('Network error: ' + error.message);
}
```

### 5. Context 활용

모든 이전 단계의 결과는 `context`에 저장되어 있습니다:

```javascript
// 전체 대화 내용을 요약할 때 사용
const summary = {
  topic: data.context.opening_topic,
  question: data.context.dilemma_question,
  choices: [
    data.context.dilemma_choice1,
    data.context.dilemma_choice2
  ],
  roles: data.context.roles_role?.split(', ')
};
```

---

## FastAPI 자동 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- **Swagger UI**: `https://dilemmai.org/docs`
- **ReDoc**: `https://dilemmai.org/redoc`

---

## 기술 스택

- **Backend**: FastAPI, Python 3.12+
- **LLM Framework**: LangChain (langchain-core 1.0.5+)
- **AI Models**: OpenAI GPT-4o-mini, DALL-E 3
- **Validation**: Pydantic 2.8+
- **Database**: MySQL with AsyncIO
- **Deployment**: Docker, Nginx

---

## 변경 이력

### v2.0.0 (2024-01-XX)
- ✨ LangChain 파싱 기능 추가
- ✨ 단계별 변수 매핑 시스템 구현
- 🔧 LangChain import 경로 업데이트 (langchain-core)
- 📝 API 명세서 전면 개편

### v1.0.0 (2023-XX-XX)
- 🎉 초기 릴리스
