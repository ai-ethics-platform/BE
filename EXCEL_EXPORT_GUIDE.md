# 실험 데이터 엑셀 Export 가이드

## 개요
실험 데이터를 엑셀(xlsx) 형식으로 다운로드할 수 있는 API 엔드포인트입니다.

## API 엔드포인트

### GET `/api/research/experiments/export/excel`

실험 데이터를 엑셀 파일로 다운로드합니다.

#### Query Parameters

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `started_only` | boolean | `true` | 시작된 게임만 포함 |
| `with_consent_only` | boolean | `true` | 동의한 사용자만 포함 |
| `topic` | string | `null` | 특정 주제로 필터링 (선택사항) |

#### 사용 예시

**기본 사용 (모든 완료된 게임, 동의한 사용자만):**
```bash
GET http://localhost:8000/api/research/experiments/export/excel
```

**모든 게임 포함 (시작 여부 무관):**
```bash
GET http://localhost:8000/api/research/experiments/export/excel?started_only=false
```

**동의 여부 무관하게 모든 데이터:**
```bash
GET http://localhost:8000/api/research/experiments/export/excel?with_consent_only=false
```

**특정 주제만 필터링:**
```bash
GET http://localhost:8000/api/research/experiments/export/excel?topic=자율주행차%20윤리
```

## 엑셀 파일 형식

### 컬럼 구조

기본 정보 (8개 컬럼):
- `episode_code`: 게임 방 코드
- `participant_id`: 참가자 ID
- `signup_date`: 사용자 가입 날짜
- `username`: 사용자 이름
- `email`: 이메일
- `date_of_birth`: 생년월일
- `gender`: 성별
- `education_level`: 교육 수준

라운드별 정보 (각 라운드당 5개 컬럼 × 5라운드 = 25개 컬럼):
- `R1_role` ~ `R5_role`: 각 라운드의 역할 (CG: 요양보호사, FAM: 가족, DEV: AI 개발자)
- `R1_individual_choice` ~ `R5_individual_choice`: 개인 선택 (0~3)
- `R1_individual_confidence` ~ `R5_individual_confidence`: 개인 확신도 (1~5)
- `R1_group_choice` ~ `R5_group_choice`: 그룹 합의 선택 (0~3)
- `R1_group_confidence` ~ `R5_group_confidence`: 그룹 합의 확신도 (1~5)

**총 컬럼 수: 33개**

### 역할 코드 매핑

현재 시스템의 역할:
- `CG`: Caregiver (요양보호사)
- `FAM`: Family (가족)
- `DEV`: Developer (AI 개발자)

### 선택 값 설명

- **choice**: 0~3 또는 1~4 (시스템에 따라 다름)
  - 특정 선택지를 나타내는 숫자
  
- **confidence**: 1~5
  - 1: 확신도 매우 낮음
  - 5: 확신도 매우 높음

## 웹 브라우저에서 다운로드

웹 브라우저에서 다음 URL에 접속하면 엑셀 파일이 자동으로 다운로드됩니다:

```
http://localhost:8000/api/research/experiments/export/excel
```

또는 프로덕션 환경:

```
https://your-domain.com/api/research/experiments/export/excel
```

## Python으로 다운로드

```python
import requests

# API 엔드포인트
url = "http://localhost:8000/api/research/experiments/export/excel"

# 파라미터 설정
params = {
    "started_only": True,
    "with_consent_only": True,
    # "topic": "자율주행차 윤리"  # 특정 주제 필터링 (선택사항)
}

# 다운로드
response = requests.get(url, params=params)

# 파일 저장
if response.status_code == 200:
    with open("experiment_data.xlsx", "wb") as f:
        f.write(response.content)
    print("엑셀 파일 다운로드 완료!")
else:
    print(f"오류: {response.status_code}")
```

## curl로 다운로드

```bash
curl -o experiment_data.xlsx "http://localhost:8000/api/research/experiments/export/excel?started_only=true&with_consent_only=true"
```

## 주의사항

1. **개인정보 보호**: 엑셀 파일에는 사용자의 개인정보가 포함되어 있으므로 안전하게 관리해야 합니다.

2. **동의 확인**: `with_consent_only=true` 옵션을 사용하면 데이터 사용 및 음성 사용에 모두 동의한 사용자만 포함됩니다.

3. **파일 이름**: 다운로드되는 파일 이름은 `experiment_data_YYYYMMDD_HHMMSS.xlsx` 형식으로 자동 생성됩니다.

4. **빈 셀**: 데이터가 없는 경우 해당 셀은 비어있습니다.

## 기존 JSON Export API

JSON 형식으로 데이터를 받고 싶다면 기존 엔드포인트를 사용할 수 있습니다:

```
GET /api/research/experiments/export
```

자세한 내용은 `RESEARCH_API_GUIDE.md`를 참고하세요.
