# 연구 데이터 분석 API 가이드

## 개요
이 문서는 AI 윤리 게임의 실험 데이터를 분석하기 위한 API 엔드포인트를 설명합니다.
연구진은 이 API를 통해 플레이어 정보, 게임 선택 데이터, 음성 녹음 데이터를 조회하고 분석할 수 있습니다.

## Base URL
```
http://localhost:8000/api/research
```

배포 환경:
```
https://your-domain.com/api/research
```

---

## API 엔드포인트

### 1. 실험 데이터 통계 요약

**GET** `/experiments/summary`

전체 실험 데이터의 통계를 조회합니다.

**Response Example:**
```json
{
  "total_users": 150,
  "users_with_full_consent": 145,
  "total_rooms": 50,
  "total_started_rooms": 45,
  "total_voice_recordings": 120,
  "total_round_choices": 450,
  "total_consensus_choices": 150,
  "generated_at": "2024-01-10T12:00:00"
}
```

---

### 2. 전체 실험 데이터 Export

**GET** `/experiments/export`

전체 실험 데이터를 페이지네이션 방식으로 조회합니다.
각 room의 참가자 정보, 선택 데이터, 음성 녹음 정보를 포함합니다.

**Query Parameters:**
- `started_only` (boolean, default: true): 완료된 게임만 포함
- `with_consent_only` (boolean, default: true): 동의한 사용자만 포함
- `skip` (int, default: 0): 건너뛸 레코드 수
- `limit` (int, default: 100, max: 1000): 페이지 크기

**Request Example:**
```bash
curl "http://localhost:8000/api/research/experiments/export?started_only=true&with_consent_only=true&skip=0&limit=50"
```

**Response Example:**
```json
{
  "rooms": [
    {
      "room_id": 1,
      "room_code": "123456",
      "title": "AI 윤리 게임 세션 1",
      "topic": "자율주행차",
      "ai_type": 1,
      "ai_name": "AI 도우미",
      "is_started": true,
      "start_time": "2024-01-10T10:00:00",
      "created_at": "2024-01-10T09:00:00",
      "participants": [
        {
          "participant_id": 1,
          "nickname": "플레이어1",
          "role_id": 1,
          "is_host": true,
          "user_data": {
            "user_id": 10,
            "username": "user1",
            "email": "user1@example.com",
            "birthdate": "1995/03",
            "gender": "남",
            "education_level": "대학생",
            "major": "공학계열",
            "data_consent": true,
            "voice_consent": true,
            "created_at": "2024-01-09T12:00:00"
          },
          "round_choices": [
            {
              "round_number": 1,
              "choice": 2,
              "subtopic": "보행자 보호",
              "confidence": 4,
              "created_at": "2024-01-10T10:15:00"
            }
          ]
        }
      ],
      "consensus_choices": [
        {
          "round_number": 1,
          "choice": 2,
          "subtopic": "보행자 보호",
          "confidence": 4,
          "created_at": "2024-01-10T10:20:00"
        }
      ],
      "voice_sessions": [
        {
          "session_id": "session_123",
          "started_at": "2024-01-10T10:00:00",
          "ended_at": "2024-01-10T10:30:00",
          "is_active": false,
          "recordings": [
            {
              "id": 1,
              "user_id": 10,
              "guest_id": null,
              "file_path": "/recordings/session_123/user_10.webm",
              "file_size": 1024000,
              "duration": 600,
              "created_at": "2024-01-10T10:30:00",
              "is_processed": true
            }
          ]
        }
      ]
    }
  ],
  "total_count": 50,
  "page": 1,
  "page_size": 50,
  "exported_at": "2024-01-10T12:00:00"
}
```

---

### 3. 특정 Room 상세 데이터 조회

**GET** `/experiments/rooms/{room_id}`

특정 room의 모든 상세 데이터를 조회합니다.

**Path Parameters:**
- `room_id` (int): Room ID

**Request Example:**
```bash
curl "http://localhost:8000/api/research/experiments/rooms/1"
```

**Response:** 위의 export API의 단일 room 객체와 동일한 구조

---

### 4. 특정 사용자의 실험 참여 데이터

**GET** `/experiments/users/{user_id}`

특정 사용자가 참여한 모든 실험 데이터를 조회합니다.

**Path Parameters:**
- `user_id` (int): User ID

**Request Example:**
```bash
curl "http://localhost:8000/api/research/experiments/users/10"
```

**Response Example:**
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
  "voice_consent": true,
  "created_at": "2024-01-09T12:00:00",
  "rooms_participated": [
    {
      "room_id": 1,
      "room_code": "123456",
      "topic": "자율주행차",
      "role_id": 1,
      "nickname": "플레이어1",
      "joined_at": "2024-01-10T09:30:00",
      "choices": [
        {
          "round_number": 1,
          "choice": 2,
          "subtopic": "보행자 보호",
          "confidence": 4
        }
      ]
    }
  ],
  "voice_recordings": [
    {
      "id": 1,
      "file_path": "/recordings/session_123/user_10.webm",
      "file_size": 1024000,
      "duration": 600,
      "created_at": "2024-01-10T10:30:00"
    }
  ]
}
```

---

### 5. 선택 데이터 분석

**GET** `/experiments/choices/analysis`

라운드별, 역할별 선택 데이터를 분석합니다.

**Query Parameters:**
- `topic` (string, optional): 특정 주제만 분석

**Request Example:**
```bash
curl "http://localhost:8000/api/research/experiments/choices/analysis?topic=자율주행차"
```

**Response Example:**
```json
{
  "round_choices": [
    {
      "round_number": 1,
      "choice": 1,
      "count": 15,
      "avg_confidence": 3.8
    },
    {
      "round_number": 1,
      "choice": 2,
      "count": 25,
      "avg_confidence": 4.2
    }
  ],
  "role_choices": [
    {
      "role_id": 1,
      "choice": 1,
      "count": 12
    },
    {
      "role_id": 1,
      "choice": 2,
      "count": 8
    }
  ]
}
```

---

### 6. 테스트 데이터 삭제

**POST** `/experiments/cleanup`

테스트 중 생성된 의미 없는 데이터를 삭제합니다.

⚠️ **주의**: 이 작업은 되돌릴 수 없습니다. 신중하게 사용하세요.

**Request Body:**
```json
{
  "room_ids": [1, 2, 3],
  "user_ids": [10, 11],
  "delete_voice_files": false
}
```

**Parameters:**
- `room_ids` (array[int], optional): 삭제할 room ID 리스트
- `user_ids` (array[int], optional): 삭제할 user ID 리스트
- `delete_voice_files` (boolean, default: false): 음성 파일도 삭제할지 여부

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/research/experiments/cleanup" \
  -H "Content-Type: application/json" \
  -d '{
    "room_ids": [1, 2, 3],
    "user_ids": [],
    "delete_voice_files": false
  }'
```

**Response Example:**
```json
{
  "deleted_rooms": 3,
  "deleted_users": 0,
  "deleted_voice_recordings": 5,
  "message": "Successfully deleted 3 rooms and 0 users"
}
```

---

## 데이터 구조 설명

### User Data
- `user_id`: 사용자 고유 ID
- `username`: 사용자명
- `email`: 이메일
- `birthdate`: 생년월 (YYYY/MM 형식)
- `gender`: 성별 ("남", "여", "기타")
- `education_level`: 교육 수준 ("고등학생", "대학생", "대학원생", "직장인", "기타")
- `major`: 전공 계열 ("인문계열", "사회계열", "자연계열", "공학계열", "예술계열", "기타")
- `data_consent`: 개인정보 활용 동의 여부
- `voice_consent`: 음성 데이터 활용 동의 여부

### Round Choice
- `round_number`: 라운드 번호 (1, 2, 3, ...)
- `choice`: 선택한 옵션 (1~4)
- `subtopic`: 해당 라운드의 세부 주제
- `confidence`: 확신도 (1~5)

### Role ID
- `1`: 요양보호사
- `2`: 가족
- `3`: AI 개발자

### AI Type
- `1`: AI 타입 1
- `2`: AI 타입 2
- `3`: AI 타입 3

---

## 데이터 Export 예제

### Python을 사용한 데이터 수집 예제

```python
import requests
import pandas as pd
import json

BASE_URL = "http://localhost:8000/api/research"

def export_all_data():
    """모든 실험 데이터를 export"""
    all_rooms = []
    skip = 0
    limit = 100
    
    while True:
        response = requests.get(
            f"{BASE_URL}/experiments/export",
            params={
                "started_only": True,
                "with_consent_only": True,
                "skip": skip,
                "limit": limit
            }
        )
        data = response.json()
        all_rooms.extend(data["rooms"])
        
        if len(data["rooms"]) < limit:
            break
        skip += limit
    
    # JSON 파일로 저장
    with open("experiment_data.json", "w", encoding="utf-8") as f:
        json.dump(all_rooms, f, ensure_ascii=False, indent=2)
    
    print(f"총 {len(all_rooms)}개의 room 데이터를 export했습니다.")
    return all_rooms

def convert_to_dataframe(rooms_data):
    """데이터를 pandas DataFrame으로 변환"""
    rows = []
    
    for room in rooms_data:
        for participant in room["participants"]:
            for choice in participant["round_choices"]:
                row = {
                    "room_id": room["room_id"],
                    "room_code": room["room_code"],
                    "topic": room["topic"],
                    "ai_type": room["ai_type"],
                    "participant_id": participant["participant_id"],
                    "nickname": participant["nickname"],
                    "role_id": participant["role_id"],
                    "round_number": choice["round_number"],
                    "choice": choice["choice"],
                    "confidence": choice["confidence"],
                    "subtopic": choice["subtopic"]
                }
                
                # 사용자 정보 추가
                if participant["user_data"]:
                    row.update({
                        "user_id": participant["user_data"]["user_id"],
                        "gender": participant["user_data"]["gender"],
                        "education_level": participant["user_data"]["education_level"],
                        "major": participant["user_data"]["major"]
                    })
                
                rows.append(row)
    
    df = pd.DataFrame(rows)
    return df

# 실행
if __name__ == "__main__":
    rooms_data = export_all_data()
    df = convert_to_dataframe(rooms_data)
    
    # CSV로 저장
    df.to_csv("experiment_analysis.csv", index=False, encoding="utf-8-sig")
    print(f"CSV 파일로 저장 완료: {len(df)} rows")
```

### R을 사용한 데이터 분석 예제

```r
library(httr)
library(jsonlite)
library(dplyr)

BASE_URL <- "http://localhost:8000/api/research"

# 데이터 가져오기
get_experiment_data <- function() {
  response <- GET(paste0(BASE_URL, "/experiments/export"),
                  query = list(started_only = TRUE,
                              with_consent_only = TRUE,
                              skip = 0,
                              limit = 1000))
  
  data <- content(response, "text", encoding = "UTF-8") %>%
    fromJSON()
  
  return(data$rooms)
}

# 데이터 분석
rooms_data <- get_experiment_data()

# 선택 분석
analyze_choices <- function() {
  response <- GET(paste0(BASE_URL, "/experiments/choices/analysis"))
  data <- content(response, "text", encoding = "UTF-8") %>%
    fromJSON()
  
  return(data)
}

analysis <- analyze_choices()
print(analysis)
```

---

## 음성 데이터 접근

음성 녹음 파일은 서버의 `/recordings` 디렉토리에 저장됩니다.
API 응답의 `file_path` 필드를 통해 파일 경로를 확인할 수 있습니다.

음성 파일 다운로드를 위한 별도의 엔드포인트가 필요한 경우, 관리자에게 문의하세요.

---

## 보안 및 권한

현재 이 API는 인증이 필요하지 않습니다. 프로덕션 환경에서는 다음과 같은 보안 조치를 추가해야 합니다:

1. API 키 인증
2. IP 화이트리스트
3. Rate limiting
4. HTTPS 사용

---

## 문의

API 사용 중 문제가 발생하거나 추가 기능이 필요한 경우, 개발팀에 문의하세요.

- Email: dev@example.com
- GitHub Issues: https://github.com/your-repo/issues
