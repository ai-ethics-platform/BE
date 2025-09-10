# 다단계 챗봇 API 사용 가이드

## 개요
여러 프롬프트가 이어지는 챗봇 시스템이 구현되었습니다. Playground에서 발급한 Prompt ID를 사용하여 단계별로 대화를 진행할 수 있습니다.

## API 엔드포인트

### 1. 다단계 챗봇 대화
```
POST /chat/multi-step
```

**요청 본문:**
```json
{
  "session_id": "unique-session-id",
  "user_input": "사용자 입력 텍스트",
  "step": "topic"  // 선택사항, 없으면 현재 단계에서 진행
}
```

**응답:**
```json
{
  "session_id": "unique-session-id",
  "current_step": "topic",
  "response_text": "AI 응답 텍스트",
  "context": {
    "topic_result": "이전 단계 결과",
    "topic_user_input": "이전 사용자 입력"
  },
  "next_step": "question",
  "is_complete": false
}
```

### 2. 세션 정보 조회
```
GET /chat/session/{session_id}
```

### 3. 세션 삭제
```
DELETE /chat/session/{session_id}
```

## 단계 순서
1. **topic** - 주제 선택
2. **question** - 질문 생성
3. **situation** - 상황 분석
4. **discussion** - 토론 진행
5. **conclusion** - 결론 도출

## 설정 방법

### 1. 환경 변수 설정
`.env` 파일에 OpenAI API 키가 설정되어 있는지 확인:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 프롬프트 ID 설정
`app/core/config.py`의 `CHATBOT_PROMPTS`에서 각 단계별 프롬프트 ID를 설정:

```python
CHATBOT_PROMPTS: Dict[str, Dict[str, str]] = {
    "topic": {
        "id": "pmpt_topic_selection",  # Playground에서 발급받은 실제 ID로 변경
        "version": "1.0"
    },
    "question": {
        "id": "pmpt_question_generation", 
        "version": "1.0"
    },
    # ... 다른 단계들
}
```

### 3. 데이터베이스 마이그레이션 실행
```bash
# 마이그레이션 파일이 이미 생성되어 있음
# 데이터베이스에 적용하려면:
python -c "
import alembic.config
import alembic.command
cfg = alembic.config.Config('alembic.ini')
alembic.command.upgrade(cfg, 'head')
"
```

## 사용 예시

### 1. 새로운 대화 시작
```javascript
// 프론트엔드에서
const sessionId = generateUniqueId(); // UUID 등으로 생성

const response = await fetch('/chat/multi-step', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    user_input: "AI 윤리에 대해 토론하고 싶어요"
  })
});
```

### 2. 다음 단계 진행
```javascript
// 같은 session_id로 계속 호출
const response = await fetch('/chat/multi-step', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    user_input: "자율주행차의 윤리적 딜레마에 대해"
  })
});
```

## 주요 특징

1. **세션 관리**: `session_id`로 대화 상태 유지
2. **컨텍스트 전달**: 이전 단계 결과가 다음 단계의 `input_variables`로 자동 전달
3. **단계별 프롬프트**: 각 단계마다 다른 Prompt ID 사용
4. **자동 진행**: 단계가 자동으로 순차적으로 진행
5. **유연한 제어**: 특정 단계로 직접 이동 가능

## 주의사항

1. Playground에서 프롬프트를 Publish한 후 실제 Prompt ID를 설정해야 합니다
2. 프롬프트에 변수(예: `{{topic}}`)가 있으면 `input_variables`에 정확히 같은 키로 채워집니다
3. 세션은 데이터베이스에 저장되므로 서버 재시작 후에도 유지됩니다
