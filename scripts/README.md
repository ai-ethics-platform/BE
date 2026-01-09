# 연구 데이터 관리 스크립트

이 폴더에는 연구진이 실험 데이터를 관리하고 분석하기 위한 스크립트들이 포함되어 있습니다.

## 스크립트 목록

### 1. `cleanup_test_data.py`
테스트 중 생성된 의미 없는 데이터를 삭제하는 스크립트입니다.

**기능:**
- 데이터 통계 보기
- 모든 room 목록 보기
- 조건에 따라 room 삭제 (시작되지 않은 room, 참가자 없는 room, 테스트 room 등)
- 음성 파일 포함 삭제 옵션

**사용법:**
```bash
python scripts/cleanup_test_data.py
```

**주의사항:**
⚠️ 삭제 작업은 되돌릴 수 없습니다. 신중하게 사용하세요!

---

### 2. `export_data_example.py`
실험 데이터를 다양한 형식으로 export하는 예제 스크립트입니다.

**기능:**
- 전체 실험 데이터를 JSON 파일로 export
- 선택 데이터를 CSV 파일로 export
- 합의 선택 데이터를 CSV 파일로 export
- 음성 녹음 데이터를 CSV 파일로 export
- 사용자 정보를 CSV 파일로 export
- 선택 데이터 분석 결과 export

**사용법:**
```bash
# 필요한 패키지 설치
pip install requests pandas

# 스크립트 실행
python scripts/export_data_example.py
```

**출력:**
- `exported_data/` 디렉토리에 다음 파일들이 생성됩니다:
  - `experiment_data_YYYYMMDD_HHMMSS.json` - 전체 데이터
  - `choices_data_YYYYMMDD_HHMMSS.csv` - 개인 선택 데이터
  - `consensus_data_YYYYMMDD_HHMMSS.csv` - 합의 선택 데이터
  - `voice_recordings_YYYYMMDD_HHMMSS.csv` - 음성 녹음 정보
  - `users_data_YYYYMMDD_HHMMSS.csv` - 사용자 정보
  - `round_analysis_YYYYMMDD_HHMMSS.csv` - 라운드별 선택 분석
  - `role_analysis_YYYYMMDD_HHMMSS.csv` - 역할별 선택 분석

---

## 사전 요구사항

### Python 패키지
```bash
pip install requests pandas
```

### API 서버 실행
스크립트를 실행하기 전에 API 서버가 실행 중이어야 합니다.

```bash
# 로컬 개발 환경
uvicorn app.main:app --reload

# 또는 Docker
docker-compose up -d
```

---

## 데이터 분석 예제

### Python으로 데이터 분석하기

```python
import pandas as pd
import matplotlib.pyplot as plt

# CSV 파일 읽기
choices_df = pd.read_csv("exported_data/choices_data_20240110_120000.csv")

# 역할별 선택 분포
role_choice_dist = choices_df.groupby(['role_id', 'choice']).size().unstack(fill_value=0)
print(role_choice_dist)

# 라운드별 평균 확신도
round_confidence = choices_df.groupby('round_number')['confidence'].mean()
print(round_confidence)

# 시각화
role_choice_dist.plot(kind='bar', stacked=True)
plt.title('Role-wise Choice Distribution')
plt.xlabel('Role ID')
plt.ylabel('Count')
plt.legend(title='Choice')
plt.show()
```

### R로 데이터 분석하기

```r
library(dplyr)
library(ggplot2)

# CSV 파일 읽기
choices_df <- read.csv("exported_data/choices_data_20240110_120000.csv")

# 역할별 선택 분포
role_choice_summary <- choices_df %>%
  group_by(role_id, choice) %>%
  summarise(count = n(), .groups = 'drop')

print(role_choice_summary)

# 시각화
ggplot(role_choice_summary, aes(x = factor(role_id), y = count, fill = factor(choice))) +
  geom_bar(stat = "identity", position = "stack") +
  labs(title = "Role-wise Choice Distribution",
       x = "Role ID",
       y = "Count",
       fill = "Choice") +
  theme_minimal()
```

---

## API 문서

더 자세한 API 사용법은 [RESEARCH_API_GUIDE.md](../RESEARCH_API_GUIDE.md)를 참조하세요.

---

## 문의

스크립트 사용 중 문제가 발생하거나 질문이 있는 경우, 개발팀에 문의하세요.
