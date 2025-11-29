# AI 윤리 챗봇 API 명세서 (프론트엔드용)

## 📋 목차
1. [개요](#개요)
2. [API 엔드포인트](#api-엔드포인트)
3. [단계 순서 및 데이터 흐름](#단계-순서-및-데이터-흐름)
4. [단계별 상세 명세](#단계별-상세-명세)
5. [에러 처리](#에러-처리)

---

## 개요

**Base URL**: `https://dilemmai.org`

**주요 엔드포인트**: `POST /chat/multi-step`

**단계 순서**: `opening → question → flip → roles → ending`

---

## API 엔드포인트

### `POST /chat/multi-step`

다단계 챗봇 대화 진행

#### Request Body

```json
{
  "session_id": "unique-session-id",
  "user_input": "사용자 입력 텍스트",
  "step": "opening",  // 선택사항 (첫 요청에만 명시, 이후는 자동 진행)
  "variable": {       // 선택사항 (테스트용 또는 특정 변수를 직접 전달할 때)
    "topic": "AI 윤리",
    "question": "...",
    "choice1": "...",
    "choice2": "..."
  }
}
```

**파라미터 설명**:
- `session_id` (필수): 세션 고유 ID
- `user_input` (필수): 사용자 입력 텍스트
- `step` (선택): 실행할 단계 지정 (첫 요청에만 사용)
- `variable` (선택): OpenAI 프롬프트에 직접 전달할 변수들 (테스트 또는 디버깅용)

#### Response

```json
{
  "session_id": "unique-session-id",
  "current_step": "opening",
  "response_text": "챗봇 응답 텍스트 (사용자에게 표시)",
  "parsed_variables": {
    // 단계별로 추출된 구조화된 변수들
  },
  "context": {
    // 전체 대화 컨텍스트 (모든 이전 단계의 결과)
  },
  "next_step": "question",  // 다음 단계 (마지막이면 null)
  "is_complete": false      // 완료 여부 (ending 단계에서 true)
}
```

---

## 단계 순서 및 데이터 흐름

```
opening → question → flip → roles → ending
```

| 단계 | 입력 변수 | 출력 변수 (parsed_variables) |
|------|----------|------------------------------|
| **opening** | 없음 | `topic` |
| **question** | `topic` | `question`, `choice1`, `choice2` |
| **flip** | `question`, `choice1`, `choice2` | `dilemma_situation`, `question`, `choice1`, `flips_agree_texts`, `choice2`, `flips_disagree_texts` |
| **roles** | flip의 6개 변수 | `char1`, `chardes1`, `char2`, `chardes2`, `char3`, `chardes3` |
| **ending** | flip의 6개 + roles의 6개 | `opening`, `char1~3`, `chardes1~3`, `dilemma_situation`, `question`, `agree_label`, `disagree_label`, `flips_agree_texts`, `flips_disagree_texts`, `agreeEnding`, `disagreeEnding` |

### 변수 전달 방식

- 백엔드는 context에 `{step}_{variable}` 형식으로 저장 (예: `opening_topic`)
- 다음 단계 호출 시 자동으로 필요한 변수를 매핑하여 OpenAI 프롬프트에 전달
- 프론트엔드는 신경 쓸 필요 없음 (백엔드가 자동 처리)

---

## 단계별 상세 명세

### 1️⃣ Opening 단계

**유저 행동**: 주제 확정

**챗봇 행동**: `parsed_variables`에 `topic` 반환

**다음 단계**: 유저가 "다음 단계" 입력 → question 단계로 이동

#### parsed_variables 구조

```typescript
{
  topic: string  // 확정된 AI 주제
}
```

#### Response 예시

```json
{
  "session_id": "session-123",
  "current_step": "opening",
  "response_text": "[챗봇이 생성한 응답 텍스트]",
  "parsed_variables": {
    "topic": "AI 윤리"
  },
  "next_step": "question",
  "is_complete": false
}
```

---

### 2️⃣ Question 단계

**입력**: opening 단계에서 받은 `topic`

**유저 행동**: 질문 확정

**챗봇 행동**: `parsed_variables`에 `question`, `choice1`, `choice2` 반환

**다음 단계**: 유저가 "다음 단계" 입력 → flip 단계로 이동 (question, choice1, choice2를 variable로 전달)

#### parsed_variables 구조

```typescript
{
  question: string   // 딜레마 질문
  choice1: string    // 선택지 1
  choice2: string    // 선택지 2
}
```

#### Response 예시

```json
{
  "session_id": "session-123",
  "current_step": "question",
  "response_text": "[챗봇이 생성한 응답 텍스트]",
  "parsed_variables": {
    "question": "AI 시스템이 최대한 정확한 결과를 제공하기 위해 어떤 선택을 해야 할까요?",
    "choice1": "정확성을 높이기 위해 특정 집단의 데이터를 우선적으로 사용할 것인가?",
    "choice2": "공정성을 위해 모든 집단에 대해 균형 잡힌 결과를 제공할 것인가?"
  },
  "next_step": "flip",
  "is_complete": false
}
```

---

### 3️⃣ Flip 단계

**입력**: question 단계에서 받은 `question`, `choice1`, `choice2`

**챗봇 행동**: 시나리오와 플립 상황 결정

**출력**: `parsed_variables`에 6개 변수 반환
- `dilemma_situation`: 상황 시나리오
- `question`: 질문
- `choice1`: 선택지 1 (agree_label)
- `flips_agree_texts`: 선택지 1에 대한 플립 자료
- `choice2`: 선택지 2 (disagree_label)
- `flips_disagree_texts`: 선택지 2에 대한 플립 자료

**다음 단계**: 유저가 "다음 단계" 입력 → roles 단계로 이동 (위 6개 변수를 전달)

#### parsed_variables 구조

```typescript
{
  dilemma_situation: string   // 상황 시나리오
  question: string            // 딜레마 질문
  choice1: string             // 선택지 1
  flips_agree_texts: string   // 선택지 1 플립 자료
  choice2: string             // 선택지 2
  flips_disagree_texts: string // 선택지 2 플립 자료
}
```

#### Response 예시

```json
{
  "session_id": "session-123",
  "current_step": "flip",
  "response_text": "[챗봇이 생성한 시나리오와 플립 상황 텍스트]",
  "parsed_variables": {
    "dilemma_situation": "AI 시스템이 학교에서 학생들의 성적을 예측하는 데 사용되고 있습니다...",
    "question": "AI 시스템이 최대한 정확한 결과를 제공하기 위해...",
    "choice1": "정확성을 높이기 위해 특정 집단의 데이터를 우선적으로 사용할 것인가?",
    "flips_agree_texts": "정확성을 높이기 위해 다수 집단의 데이터를 우선적으로 사용한 결과...",
    "choice2": "공정성을 위해 모든 집단에 대해 균형 잡힌 결과를 제공할 것인가?",
    "flips_disagree_texts": "모든 집단에 대해 균형 잡힌 결과를 제공하기 위해 데이터의 균형을 맞춘 결과..."
  },
  "next_step": "roles",
  "is_complete": false
}
```

---

### 4️⃣ Roles 단계

**입력**: flip 단계에서 받은 6개 변수
- `dilemma_situation`, `question`, `choice1`, `flips_agree_texts`, `choice2`, `flips_disagree_texts`

**챗봇 행동**: 역할극 인물 3명 설계

**출력**: `parsed_variables`에 6개 변수 반환
- `char1`, `charDes1`: 역할 1 이름 및 배경 설명
- `char2`, `charDes2`: 역할 2 이름 및 배경 설명
- `char3`, `charDes3`: 역할 3 이름 및 배경 설명

**다음 단계**: 유저가 "다음 단계" 입력 → ending 단계로 이동 (flip 6개 + roles 6개 변수 전달)

#### parsed_variables 구조

```typescript
{
  char1: string      // 역할 1 이름
  chardes1: string   // 역할 1 배경 설명
  char2: string      // 역할 2 이름
  chardes2: string   // 역할 2 배경 설명
  char3: string      // 역할 3 이름
  chardes3: string   // 역할 3 배경 설명
}
```

#### Response 예시

```json
{
  "session_id": "session-123",
  "current_step": "roles",
  "response_text": "[챗봇이 생성한 역할 제안 텍스트]",
  "parsed_variables": {
    "char1": "학생",
    "chardes1": "당신은 중학교 3학년 학생이며, AI 시스템의 성적 예측 방식에 대해 잘 알고 있습니다...",
    "char2": "교사",
    "chardes2": "당신은 10년 경력의 고등학교 교사입니다...",
    "char3": "학부모",
    "chardes3": "당신은 중학교 1학년 자녀를 둔 학부모로..."
  },
  "next_step": "ending",
  "is_complete": false
}
```

---

### 5️⃣ Ending 단계

**입력**: flip 단계의 6개 변수 + roles 단계의 6개 변수 (총 12개)

**챗봇 행동**: 최종 템플릿 완성 (오프닝, 역할, 시나리오, 질문, 선택지, 플립 자료, 최종 멘트 포함)

**출력**: `parsed_variables`에 15개 변수 반환

**완료**: `is_complete: true`, `next_step: null`

#### parsed_variables 구조

```typescript
{
  opening: string[]            // 오프닝 멘트 (문장 배열)
  char1: string                // 역할 1 이름
  chardes1: string             // 역할 1 배경 설명
  char2: string                // 역할 2 이름
  chardes2: string             // 역할 2 배경 설명
  char3: string                // 역할 3 이름
  chardes3: string             // 역할 3 배경 설명
  dilemma_situation: string[]  // 상황 시나리오 (문장 배열)
  question: string             // 딜레마 질문
  agree_label: string          // 선택지 1 라벨
  disagree_label: string       // 선택지 2 라벨
  flips_agree_texts: string[]  // 선택지 1 플립 자료 (문장 배열)
  flips_disagree_texts: string[] // 선택지 2 플립 자료 (문장 배열)
  agreeEnding: string          // 선택지 1 최종 멘트
  disagreeEnding: string       // 선택지 2 최종 멘트
}
```

#### Response 예시

```json
{
  "session_id": "session-123",
  "current_step": "ending",
  "response_text": "[챗봇이 생성한 최종 초안 텍스트]",
  "parsed_variables": {
    "opening": [
      "학교의 AI 시스템이 도입된 지 한 달이 지났습니다.",
      "학생들의 성적을 예측하고 관리하기 위해 설계된 이 시스템은 학부모와 교사들 사이에서 기대와 우려를 동시에 불러일으키고 있습니다.",
      "오늘, 학교는 반대와 찬성을 나누는 공청회를 개최하기로 하였고, 이 자리에는 AI 시스템 개발자, 학생 대표, 그리고 학부모가 모였습니다.",
      "여러분은 각자의 입장에서 이 신기술의 윤리적 문제를 토론하게 될 것입니다."
    ],
    "char1": "AI 시스템 개발자",
    "chardes1": "당신은 한 대학교의 컴퓨터 공학과에서 AI 시스템을 연구하는 교수입니다...",
    "char2": "학생 대표",
    "chardes2": "당신은 고등학교 3학년 학생으로, 학교의 학생회에서 활동하고 있습니다...",
    "char3": "학부모",
    "chardes3": "당신은 중학생을 둔 부모로, 자녀의 교육과 안전에 관심이 많습니다...",
    "dilemma_situation": [
      "AI 시스템이 학교에서 학생들의 성적을 예측하는 데 사용되고 있습니다.",
      "이 시스템은 처음 도입될 때 학생들의 개인적인 성향과 반응을 고려하지 않고, 객관적인 데이터를 기반으로 결과를 도출하기 위해 설계되었습니다.",
      "최근 이 시스템의 정확성을 높이기 위한 새로운 방안이 제시되었고, 그 과정에서 특정 집단의 데이터를 우선적으로 사용해야 한다는 논의가 일기 시작했습니다.",
      "그러나 이로 인해 공정성과 차별적인 결과에 대한 우려가 커지고 있습니다."
    ],
    "question": "AI 시스템이 최대한 정확한 결과를 제공하기 위해 어떤 선택을 해야 할까요?",
    "agree_label": "정확성을 높이기 위해 특정 집단의 데이터를 우선적으로 사용할 것인가?",
    "disagree_label": "공정성을 위해 모든 집단에 대해 균형 잡힌 결과를 제공할 것인가?",
    "flips_agree_texts": [
      "정확성을 높이기 위해 다수 집단의 데이터를 우선적으로 사용한 결과, 특정 집단이 과소평가되고 차별받는 상황이 발생했습니다.",
      "이는 학부모와 학생들 사이에서 큰 논란이 일어나게 했으며, 결국 학교는 신뢰를 잃게 됩니다."
    ],
    "flips_disagree_texts": [
      "모든 집단에 대해 균형 잡힌 결과를 제공하기 위해 데이터의 균형을 맞춘 결과, 시스템이 일부 학생들에게 연결되는 지표가 왜곡되어 그들의 성적 예측에 부정적인 영향을 미쳤습니다.",
      "이로 인해 학생들의 불만이 커지고, 교사들도 예측에 혼란을 겪게 됩니다."
    ],
    "agreeEnding": "우리는 정확성을 우선시한다고 결정하였고, 그 결과 얻은 정보는 있었지만, 공정성을 잃어 학생들과 학부모의 신뢰를 무너뜨리게 되었습니다. 여러분은 기술적 성과와 윤리적 문제 가운데 어떤 쪽을 더 중요하게 생각하시나요?",
    "disagreeEnding": "우리는 공정성을 우선시한다고 결정하였고, 그것이 학생들의 기대를 만족시켰지만, 예측 시스템의 신뢰성은 낮아지게 되었습니다. 여러분은 신뢰와 정확성 중 어떤 가치를 더 중시하나요?"
  },
  "next_step": null,
  "is_complete": true
}
```

---

## 프론트엔드 처리 가이드

### 기본 흐름

```javascript
// 1. 세션 시작 (opening 단계)
const sessionId = generateUniqueId();
const response1 = await fetch('/chat/multi-step', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    user_input: "AI 윤리에 대해 토론하고 싶어요",
    step: 'opening'
  })
});
const data1 = await response1.json();
// data1.parsed_variables.topic 사용

// 2. 다음 단계로 진행 (step 생략 시 자동 진행)
const response2 = await fetch('/chat/multi-step', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    user_input: "다음 단계"
  })
});
const data2 = await response2.json();
// data2.current_step === 'question'
// data2.parsed_variables.question, choice1, choice2 사용
```

### parsed_variables 처리

```javascript
// parsed_variables가 비어있을 수 있으므로 항상 체크
if (data.parsed_variables && Object.keys(data.parsed_variables).length > 0) {
  // 구조화된 데이터 사용
  processStructuredData(data.parsed_variables);
} else {
  // 파싱 실패 시 원본 텍스트 사용
  displayRawText(data.response_text);
}
```

### variable 필드 사용 (테스트/디버깅)

```javascript
// 특정 단계를 바로 테스트하고 싶을 때 (이전 단계 없이)
const response = await fetch('/chat/multi-step', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    user_input: "시작",
    step: "flip",
    variable: {
      question: "AI가 학생 성적을 예측하는 상황에서 어떤 선택을 해야 할까요?",
      choice1: "정확성을 위해 특정 집단의 데이터를 우선 사용한다",
      choice2: "공정성을 위해 모든 집단에 균형 잡힌 결과를 제공한다"
    }
  })
});
// variable로 전달한 값이 프롬프트에 직접 전달됨
```

**주의**: `variable` 필드는 주로 개발/테스트 용도입니다. 프로덕션에서는 일반적으로 사용하지 않으며, 백엔드가 자동으로 context에서 필요한 변수를 가져옵니다.

### ending 단계 처리 예시

```javascript
if (data.is_complete && data.parsed_variables) {
  const template = {
    opening: data.parsed_variables.opening,
    roles: [
      { name: data.parsed_variables.char1, description: data.parsed_variables.chardes1 },
      { name: data.parsed_variables.char2, description: data.parsed_variables.chardes2 },
      { name: data.parsed_variables.char3, description: data.parsed_variables.chardes3 }
    ],
    scenario: data.parsed_variables.dilemma_situation,
    question: data.parsed_variables.question,
    choices: [
      {
        label: data.parsed_variables.agree_label,
        flipTexts: data.parsed_variables.flips_agree_texts,
        ending: data.parsed_variables.agreeEnding
      },
      {
        label: data.parsed_variables.disagree_label,
        flipTexts: data.parsed_variables.flips_disagree_texts,
        ending: data.parsed_variables.disagreeEnding
      }
    ]
  };
  
  // 템플릿 사용
  createGameTemplate(template);
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

| 코드 | 의미 | 대응 방법 |
|------|------|----------|
| `200` | 성공 | 정상 처리 |
| `400` | Bad Request | 요청 파라미터 확인 |
| `500` | Internal Server Error | 재시도 또는 사용자에게 알림 |
| `502` | Bad Gateway | OpenAI API 오류, 재시도 |

### parsed_variables가 빈 객체인 경우

LangChain 파싱이 실패해도 에러를 발생시키지 않고 빈 객체를 반환합니다.

```json
{
  "parsed_variables": {},
  "response_text": "원본 응답 텍스트"
}
```

**처리 방법**: `response_text`를 사용하여 사용자에게 표시

---

## 세션 관리 API

### 세션 정보 조회

```
GET /chat/session/{session_id}
```

### 세션 삭제

```
DELETE /chat/session/{session_id}
```

---

## 기타 API

### 이미지 생성

```
POST /chat/image
```

상세한 내용은 별도 문서 참조

---

## 요약

### 각 단계별 핵심

| 단계 | 유저 행동 | 백엔드 출력 (parsed_variables) | 비고 |
|------|----------|------------------------------|------|
| opening | 주제 확정 | `topic` | 첫 단계 |
| question | 질문 확정 | `question`, `choice1`, `choice2` | topic 사용 |
| flip | "다음 단계" | 6개 변수 (시나리오+플립) | question, choice1, choice2 사용 |
| roles | "다음 단계" | 6개 변수 (역할 정보) | flip의 6개 변수 사용 |
| ending | "다음 단계" | 15개 변수 (최종 템플릿) | flip 6개 + roles 6개 사용, is_complete=true |

### 핵심 포인트

1. **session_id**: 모든 요청에 동일한 session_id 사용
2. **step 생략**: 첫 요청만 `step: "opening"` 명시, 이후는 생략하면 자동 진행
3. **parsed_variables**: 구조화된 데이터, 비어있을 수 있음
4. **response_text**: 항상 사용자에게 표시할 텍스트 포함
5. **is_complete**: ending 단계에서 true, 템플릿 완성 시그널

---

## 변경 이력

### v3.0.0 (2025-01-XX)
- 🔄 단계 순서 변경: `opening → question → flip → roles → ending`
- ✨ flip 단계 확장: 6개 변수 추출 (시나리오+플립)
- ✨ roles 단계 확장: 6개 변수 추출 (역할 정보)
- ✨ ending 단계 확장: 15개 변수 추출 (최종 템플릿)
- 📝 API 명세서 간소화 및 재작성
