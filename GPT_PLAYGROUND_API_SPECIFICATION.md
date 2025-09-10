# GPT Playground API 명세서

## 개요
OpenAI Playground에서 발급한 Prompt ID를 사용하여 여러 프롬프트가 이어지는 다단계 챗봇 시스템입니다. 각 단계별로 다른 프롬프트를 호출하고, 이전 단계의 결과를 다음 단계의 컨텍스트로 전달합니다.

## 시스템 아키텍처

### 1. 데이터베이스 스키마

#### ChatSession 테이블
```sql
CREATE TABLE chat_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    current_step VARCHAR(50) NOT NULL DEFAULT 'topic',
    context JSON NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_id (id)
);
```

### 2. 설정 구조

#### 환경 변수 (.env)
```bash
# OpenAI API 설정
OPENAI_API_KEY=sk-your-openai-api-key-here

# 기타 설정들...
SECRET_KEY=your-secret-key
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=ai_ethics_db
```

#### 프롬프트 매핑 설정 (app/core/config.py)
```python
CHATBOT_PROMPTS: Dict[str, Dict[str, str]] = {
    "topic": {
        "id": "pmpt_topic_selection",      # Playground에서 발급받은 실제 ID
        "version": "1.0"                   # Publish된 버전
    },
    "question": {
        "id": "pmpt_question_generation", 
        "version": "1.0"
    },
    "situation": {
        "id": "pmpt_situation_analysis",
        "version": "1.0"
    },
    "discussion": {
        "id": "pmpt_discussion_facilitation",
        "version": "1.0"
    },
    "conclusion": {
        "id": "pmpt_conclusion_synthesis",
        "version": "1.0"
    }
}
```

## API 엔드포인트 상세 명세

### 1. 다단계 챗봇 대화

#### POST /chat/multi-step

**설명**: 다단계 챗봇과의 대화를 진행합니다. 세션 기반으로 상태를 유지하며, 단계별로 다른 프롬프트를 호출합니다.

**요청 헤더**:
```
Content-Type: application/json
```

**요청 본문**:
```json
{
  "session_id": "string",     // 필수: 세션 식별자 (UUID 권장)
  "user_input": "string",     // 필수: 사용자 입력 텍스트
  "step": "string"            // 선택: 특정 단계로 직접 이동 (topic|question|situation|discussion|conclusion)
}
```

**요청 예시**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_input": "AI 윤리에 대해 토론하고 싶어요",
  "step": "topic"
}
```

**응답 본문**:
```json
{
  "session_id": "string",           // 세션 식별자
  "current_step": "string",         // 현재 실행된 단계
  "response_text": "string",        // AI 응답 텍스트
  "context": {                      // 업데이트된 컨텍스트 (이전 단계 결과들)
    "topic_result": "string",       // topic 단계 결과
    "topic_user_input": "string",   // topic 단계 사용자 입력
    "question_result": "string",    // question 단계 결과
    "question_user_input": "string" // question 단계 사용자 입력
  },
  "next_step": "string",            // 다음 단계 (null이면 마지막 단계)
  "is_complete": boolean            // 대화 완료 여부
}
```

**응답 예시**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_step": "topic",
  "response_text": "AI 윤리 토론을 시작하겠습니다. 어떤 주제에 대해 논의하고 싶으신가요? 예를 들어, 자율주행차의 윤리적 딜레마, AI의 편향성, 개인정보 보호 등 다양한 주제가 있습니다.",
  "context": {
    "topic_result": "AI 윤리 토론을 시작하겠습니다. 어떤 주제에 대해 논의하고 싶으신가요? 예를 들어, 자율주행차의 윤리적 딜레마, AI의 편향성, 개인정보 보호 등 다양한 주제가 있습니다.",
    "topic_user_input": "AI 윤리에 대해 토론하고 싶어요"
  },
  "next_step": "question",
  "is_complete": false
}
```

**HTTP 상태 코드**:
- `200 OK`: 성공
- `400 Bad Request`: 잘못된 요청 (예: 필수 필드 누락, 잘못된 단계명)
- `500 Internal Server Error`: 서버 오류 (예: OpenAI API 오류, 데이터베이스 오류)

**에러 응답 예시**:
```json
{
  "detail": "No prompt configuration found for step: invalid_step"
}
```

### 2. 세션 정보 조회

#### GET /chat/session/{session_id}

**설명**: 특정 세션의 현재 상태와 컨텍스트를 조회합니다.

**경로 매개변수**:
- `session_id` (string): 조회할 세션의 식별자

**요청 예시**:
```
GET /chat/session/550e8400-e29b-41d4-a716-446655440000
```

**응답 본문**:
```json
{
  "session_id": "string",
  "current_step": "string",
  "context": {
    "topic_result": "string",
    "topic_user_input": "string"
  },
  "created_at": "2025-01-27T12:00:00Z",
  "updated_at": "2025-01-27T12:05:00Z"
}
```

**HTTP 상태 코드**:
- `200 OK`: 성공
- `500 Internal Server Error`: 서버 오류

### 3. 세션 삭제

#### DELETE /chat/session/{session_id}

**설명**: 특정 세션과 관련된 모든 데이터를 삭제합니다.

**경로 매개변수**:
- `session_id` (string): 삭제할 세션의 식별자

**요청 예시**:
```
DELETE /chat/session/550e8400-e29b-41d4-a716-446655440000
```

**응답 본문**:
```json
{
  "message": "Session 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

**HTTP 상태 코드**:
- `200 OK`: 성공
- `500 Internal Server Error`: 서버 오류

## 단계별 워크플로우

### 1. 단계 순서
```
topic → question → situation → discussion → conclusion
```

### 2. 각 단계별 역할

#### Topic 단계
- **목적**: 토론 주제 선택 및 설정
- **입력**: 사용자의 관심 주제
- **출력**: 구체적인 토론 주제 제안
- **컨텍스트 저장**: `topic_result`, `topic_user_input`

#### Question 단계
- **목적**: 선택된 주제에 대한 핵심 질문 생성
- **입력**: 사용자의 주제 선택
- **출력**: 윤리적 딜레마를 다루는 핵심 질문들
- **컨텍스트 저장**: `question_result`, `question_user_input`

#### Situation 단계
- **목적**: 구체적인 상황 시나리오 제시
- **입력**: 사용자의 질문 선택
- **출력**: 현실적인 상황 시나리오
- **컨텍스트 저장**: `situation_result`, `situation_user_input`

#### Discussion 단계
- **목적**: 토론 진행 및 다양한 관점 제시
- **입력**: 사용자의 상황에 대한 반응
- **출력**: 다양한 윤리적 관점과 토론 가이드
- **컨텍스트 저장**: `discussion_result`, `discussion_user_input`

#### Conclusion 단계
- **목적**: 토론 결론 및 학습 정리
- **입력**: 사용자의 최종 의견
- **출력**: 토론 요약 및 윤리적 통찰
- **컨텍스트 저장**: `conclusion_result`, `conclusion_user_input`

## OpenAI API 연동 상세

### 1. Responses API 호출 구조
```python
response = openai_client.responses.create(
    prompt={
        "id": "pmpt_topic_selection",    # Playground에서 발급받은 Prompt ID
        "version": "1.0"                 # Publish된 버전
    },
    input="사용자 입력 텍스트",
    input_variables={
        "topic_result": "이전 단계 결과",
        "topic_user_input": "이전 사용자 입력",
        "user_input": "현재 사용자 입력"
    }
)
```

### 2. 응답 텍스트 추출 로직
```python
text_parts = []
for item in response.output or []:
    for c in item.content or []:
        if c.type == "output_text":
            text_parts.append(c.text)
response_text = "".join(text_parts).strip()
```

## 프론트엔드 통합 가이드

### 1. 기본 사용법
```javascript
class ChatbotClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.sessionId = this.generateSessionId();
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    async sendMessage(userInput, step = null) {
        const response = await fetch(`${this.baseUrl}/chat/multi-step`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: this.sessionId,
                user_input: userInput,
                step: step
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async getSessionInfo() {
        const response = await fetch(`${this.baseUrl}/chat/session/${this.sessionId}`);
        return await response.json();
    }
    
    async deleteSession() {
        const response = await fetch(`${this.baseUrl}/chat/session/${this.sessionId}`, {
            method: 'DELETE'
        });
        return await response.json();
    }
}

// 사용 예시
const chatbot = new ChatbotClient();

// 첫 번째 메시지
const response1 = await chatbot.sendMessage("AI 윤리에 대해 토론하고 싶어요");
console.log(response1.response_text);

// 두 번째 메시지 (자동으로 다음 단계로 진행)
const response2 = await chatbot.sendMessage("자율주행차의 윤리적 딜레마에 대해");
console.log(response2.response_text);
```

### 2. React 컴포넌트 예시
```jsx
import React, { useState, useEffect } from 'react';

const ChatbotComponent = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [sessionId] = useState(() => 'session_' + Date.now());
    const [currentStep, setCurrentStep] = useState('topic');
    const [isComplete, setIsComplete] = useState(false);
    
    const sendMessage = async () => {
        if (!input.trim()) return;
        
        try {
            const response = await fetch('/chat/multi-step', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    user_input: input,
                    step: currentStep
                })
            });
            
            const data = await response.json();
            
            setMessages(prev => [
                ...prev,
                { type: 'user', content: input },
                { type: 'bot', content: data.response_text }
            ]);
            
            setCurrentStep(data.next_step || data.current_step);
            setIsComplete(data.is_complete);
            setInput('');
            
        } catch (error) {
            console.error('Error:', error);
        }
    };
    
    return (
        <div className="chatbot-container">
            <div className="messages">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.type}`}>
                        {msg.content}
                    </div>
                ))}
            </div>
            
            <div className="input-area">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder={isComplete ? "대화가 완료되었습니다" : "메시지를 입력하세요..."}
                    disabled={isComplete}
                />
                <button onClick={sendMessage} disabled={isComplete || !input.trim()}>
                    전송
                </button>
            </div>
            
            <div className="status">
                현재 단계: {currentStep} {isComplete && "(완료)"}
            </div>
        </div>
    );
};
```

## 에러 처리 및 디버깅

### 1. 일반적인 에러 상황

#### OpenAI API 키 누락
```json
{
  "detail": "OPENAI_API_KEY is not configured"
}
```
**해결방법**: `.env` 파일에 올바른 API 키 설정

#### 잘못된 Prompt ID
```json
{
  "detail": "No prompt configuration found for step: topic"
}
```
**해결방법**: `app/core/config.py`의 `CHATBOT_PROMPTS`에서 올바른 Prompt ID 설정

#### OpenAI API 오류
```json
{
  "detail": "OpenAI API call failed: Invalid prompt ID"
}
```
**해결방법**: Playground에서 프롬프트가 올바르게 Publish되었는지 확인

### 2. 디버깅 팁

#### 세션 상태 확인
```bash
curl -X GET "http://localhost:8000/chat/session/your-session-id"
```

#### 로그 확인
서버 로그에서 다음 정보를 확인:
- OpenAI API 호출 상태
- 데이터베이스 연결 상태
- 세션 생성/업데이트 상태

## 보안 고려사항

### 1. API 키 보안
- `.env` 파일을 `.gitignore`에 추가
- 프로덕션 환경에서는 환경 변수로 설정
- API 키를 클라이언트에 노출하지 않음

### 2. 세션 보안
- 세션 ID는 예측하기 어려운 값 사용 (UUID 권장)
- 세션 데이터는 서버에서만 관리
- 민감한 정보는 컨텍스트에 저장하지 않음

### 3. 입력 검증
- 사용자 입력 길이 제한
- 특수 문자 필터링
- SQL 인젝션 방지 (SQLAlchemy ORM 사용)

## 성능 최적화

### 1. 데이터베이스 최적화
- 세션 ID에 인덱스 설정
- 오래된 세션 정리 작업 (Cron Job)
- 연결 풀 설정

### 2. API 응답 최적화
- 비동기 처리로 응답 시간 단축
- OpenAI API 호출 최적화
- 불필요한 데이터 전송 최소화

## 배포 가이드

### 1. 환경 설정
```bash
# .env 파일 설정
OPENAI_API_KEY=sk-your-actual-api-key
SECRET_KEY=your-secret-key
DB_HOST=your-db-host
DB_PASSWORD=your-db-password
```

### 2. 데이터베이스 마이그레이션
```bash
# 마이그레이션 실행
python -c "
import alembic.config
import alembic.command
cfg = alembic.config.Config('alembic.ini')
alembic.command.upgrade(cfg, 'head')
"
```

### 3. 서버 실행
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 모니터링 및 로깅

### 1. 주요 메트릭
- API 응답 시간
- OpenAI API 호출 성공률
- 세션 생성/삭제 수
- 에러 발생률

### 2. 로그 레벨
- INFO: 정상적인 API 호출
- WARNING: OpenAI API 지연
- ERROR: API 호출 실패, 데이터베이스 오류
- DEBUG: 상세한 디버깅 정보

이 명세서를 통해 GPT Playground API를 완전히 이해하고 구현할 수 있습니다.
