# 연구 데이터 분석 API 구현 완료 보고서

## 📋 요청사항 분석

연구진이 실험 데이터를 분석할 수 있도록 다음 요구사항을 충족하는 API를 개발했습니다:

1. ✅ 플레이어 회원 가입 정보 조회
2. ✅ 게임 내 모든 선택 결과 데이터 연동 조회
3. ✅ 음성 데이터 접근 가능
4. ✅ 테스트 데이터 삭제 기능

---

## 🎯 구현 내용

### 1. 연구 데이터 분석 API 엔드포인트

**파일:** `app/api/endpoints/research.py`

#### 주요 엔드포인트:

1. **GET `/api/research/experiments/summary`**
   - 전체 실험 데이터 통계 요약
   - 사용자 수, 게임 세션 수, 음성 녹음 수 등

2. **GET `/api/research/experiments/export`**
   - 전체 실험 데이터 export (페이지네이션 지원)
   - 사용자 정보, 게임 선택, 음성 녹음 정보 모두 포함
   - 필터링: 완료된 게임만, 동의한 사용자만

3. **GET `/api/research/experiments/rooms/{room_id}`**
   - 특정 room의 상세 데이터 조회
   - 모든 참가자, 선택, 음성 녹음 포함

4. **GET `/api/research/experiments/users/{user_id}`**
   - 특정 사용자의 모든 실험 참여 데이터

5. **GET `/api/research/experiments/choices/analysis`**
   - 라운드별, 역할별 선택 데이터 분석
   - 확신도 평균 등 통계 제공

6. **POST `/api/research/experiments/cleanup`**
   - 테스트 데이터 삭제 (⚠️ 되돌릴 수 없음)
   - room 단위 삭제, user 단위 삭제
   - 음성 파일 포함 삭제 옵션

---

### 2. 데이터 스키마

**파일:** `app/schemas/research.py`

정의된 스키마:
- `UserDataExport`: 사용자 정보 (인구통계학 정보, 동의 여부)
- `RoundChoiceData`: 라운드별 개인 선택
- `ConsensusChoiceData`: 라운드별 합의 선택
- `VoiceRecordingData`: 음성 녹음 파일 정보
- `RoomDataExport`: 전체 room 데이터
- `ExperimentDataResponse`: API 응답 형식
- `DeleteTestDataRequest/Response`: 데이터 삭제 요청/응답

---

### 3. Docker 구성 업데이트

**파일:** `docker-compose.yml`

변경사항:
- MySQL 8.0 데이터베이스 서비스 추가
- 영구 볼륨 설정 (`mysql_data`)
- 환경 변수를 통한 데이터베이스 설정
- Backend에 MySQL 의존성 추가

---

### 4. 연구진용 스크립트

#### `scripts/cleanup_test_data.py`
테스트 데이터 삭제를 위한 대화형 스크립트
- 데이터 통계 보기
- 조건별 room 삭제 (시작 안 된 room, 참가자 없는 room, 테스트 room)
- 안전한 삭제 확인 절차

#### `scripts/export_data_example.py`
데이터를 다양한 형식으로 export하는 예제
- JSON: 전체 데이터
- CSV: 선택 데이터, 합의 데이터, 음성 녹음, 사용자 정보
- 분석 결과 export
- pandas를 활용한 데이터 변환

---

### 5. 문서화

#### `RESEARCH_API_GUIDE.md`
연구진을 위한 상세 API 가이드
- 모든 엔드포인트 설명
- 요청/응답 예제
- Python/R 데이터 분석 예제
- 데이터 구조 설명

#### `scripts/README.md`
스크립트 사용 가이드
- 각 스크립트의 기능 설명
- 사용법 및 예제
- 데이터 분석 방법

#### `README.md` 업데이트
메인 README에 연구 API 정보 추가

---

## 📊 데이터 구조

### 사용자 정보 (User Data)
```json
{
  "user_id": 10,
  "username": "user1",
  "email": "user1@example.com",
  "birthdate": "1995/03",
  "gender": "남",
  "education_level": "대학생",
  "major": "공학계열",
  "data_consent": true,
  "voice_consent": true
}
```

### 게임 선택 데이터 (Round Choice)
```json
{
  "round_number": 1,
  "choice": 2,
  "subtopic": "보행자 보호",
  "confidence": 4,
  "created_at": "2024-01-10T10:15:00"
}
```

### 음성 녹음 데이터 (Voice Recording)
```json
{
  "id": 1,
  "user_id": 10,
  "file_path": "/recordings/session_123/user_10.webm",
  "file_size": 1024000,
  "duration": 600,
  "created_at": "2024-01-10T10:30:00"
}
```

---

## 🔗 데이터 연동

API는 다음과 같이 데이터를 연동합니다:

```
User (회원가입 정보)
  ↓
RoomParticipant (게임 참가 정보)
  ↓
├─ RoundChoice (라운드별 개인 선택)
├─ ConsensusChoice (라운드별 합의 선택)
└─ VoiceRecording (음성 녹음 파일)
```

모든 데이터는 `user_id`를 통해 연결되어 있으며, 한 번의 API 호출로 관련된 모든 데이터를 조회할 수 있습니다.

---

## 💻 사용 예제

### 1. 전체 데이터 조회
```bash
curl "http://localhost:8000/api/research/experiments/export?started_only=true&with_consent_only=true&skip=0&limit=100"
```

### 2. 특정 사용자 데이터 조회
```bash
curl "http://localhost:8000/api/research/experiments/users/10"
```

### 3. 테스트 데이터 삭제
```bash
python scripts/cleanup_test_data.py
```

### 4. 데이터 export (CSV/JSON)
```bash
python scripts/export_data_example.py
```

---

## 🔒 보안 고려사항

현재 구현은 개발/연구 환경을 위한 것입니다. 프로덕션 배포 시 다음을 추가해야 합니다:

1. **인증/인가**: API 키 또는 JWT 토큰 기반 인증
2. **접근 제어**: 연구진만 접근 가능하도록 역할 기반 접근 제어
3. **Rate Limiting**: API 남용 방지
4. **감사 로그**: 데이터 접근 및 삭제 이력 기록
5. **HTTPS**: 프로덕션 환경에서는 필수

---

## 📝 테스트 데이터 삭제 절차

1. **데이터 백업** (선택사항)
   ```bash
   python scripts/export_data_example.py
   ```

2. **삭제할 데이터 확인**
   ```bash
   python scripts/cleanup_test_data.py
   # 메뉴에서 "2. 모든 room 목록 보기" 선택
   ```

3. **조건에 맞는 데이터 삭제**
   ```bash
   # 메뉴에서 "3. 조건에 따라 room 삭제" 선택
   # 원하는 조건 선택 (예: 시작 안 된 room, 테스트 room 등)
   ```

4. **결과 확인**
   ```bash
   # 메뉴에서 "1. 데이터 통계 보기" 선택
   ```

---

## 🚀 배포 방법

### Docker Compose 사용
```bash
# .env 파일 설정
cp .env.example .env
# .env 파일에서 DB_PASSWORD 등 설정

# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# API 문서 확인
# http://localhost:8000/docs
```

---

## 📞 문의

API 사용 중 문제가 발생하거나 추가 기능이 필요한 경우:

1. API 문서: http://localhost:8000/docs
2. 연구 API 가이드: [RESEARCH_API_GUIDE.md](./RESEARCH_API_GUIDE.md)
3. 개발팀 이메일: dev@example.com

---

## ✅ 완료된 작업 체크리스트

- [x] 연구 데이터 분석 API 엔드포인트 구현
- [x] 데이터 스키마 정의
- [x] API 라우터에 엔드포인트 등록
- [x] Docker Compose에 MySQL 추가
- [x] 테스트 데이터 삭제 기능 구현
- [x] 데이터 export 스크립트 작성
- [x] API 사용 가이드 문서 작성
- [x] 스크립트 사용 가이드 작성
- [x] 데이터 연동 구조 문서화

---

**구현 완료일:** 2024년 1월 10일
