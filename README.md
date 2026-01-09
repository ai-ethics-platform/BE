# AI 윤리게임 백엔드
FastAPI를 이용한 AI 윤리게임 백엔드 서버입니다.

## 기술 스택
- Python 3.9+
- FastAPI
- MySQL
- OpenAI API (GPT playground)
- Docker
- GitHub Actions
- WebSocket, Redis

## 주요 기능
- 사용자 인증 및 관리
- 실시간 게임 세션 관리
- 음성 데이터 처리 및 분석
- AI 피드백 생성
- 연구 데이터 분석 API (실험 데이터 export 및 분석)

## 설치 및 실행 방법
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 수정하여 필요한 API 키와 설정 입력

# 서버 실행
uvicorn app.main:app --reload
```

## API 문서
- **메인 API 문서**: http://localhost:8000/docs (FastAPI Swagger UI)
- **연구 데이터 분석 API**: [RESEARCH_API_GUIDE.md](./RESEARCH_API_GUIDE.md)
- **챗봇 API**: [CHATBOT_API_GUIDE.md](./CHATBOT_API_GUIDE.md)
- **GPT Playground API**: [GPT_PLAYGROUND_API_SPECIFICATION.md](./GPT_PLAYGROUND_API_SPECIFICATION.md)

## Docker 실행
```bash
# 환경 변수 파일 설정
cp .env.example .env
# .env 파일 수정

# Docker Compose로 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

## 배포
Docker와 GitHub Actions를 통해 자동 배포됩니다. 

# URL !
https://www.dilemmai-idl.com/
