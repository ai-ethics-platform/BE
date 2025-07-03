# AI Ethics Game Backend 배포 가이드

## 🚀 AWS EC2 + GitHub Actions 자동 배포

### 1. AWS RDS 데이터베이스 생성

#### 1.1 RDS 인스턴스 생성
- **엔진**: MySQL 8.0
- **템플릿**: 개발/테스트
- **인스턴스 식별자**: `ai-ethics-db`
- **마스터 사용자명**: `admin`
- **마스터 비밀번호**: 강력한 비밀번호 설정
- **인스턴스 크기**: `db.t3.micro` (무료 티어)
- **스토리지**: 20GB
- **퍼블릭 액세스**: 예
- **VPC**: 기본 VPC
- **보안 그룹**: MySQL 포트(3306) 허용

#### 1.2 데이터베이스 생성 후 얻을 정보
- **엔드포인트**: `ai-ethics-db.xxxxx.ap-northeast-2.rds.amazonaws.com`
- **포트**: 3306
- **데이터베이스명**: `ai_ethics_db`
- **사용자명**: `admin`
- **비밀번호**: 설정한 비밀번호

### 2. EC2 인스턴스 생성

#### 2.1 EC2 인스턴스 설정
- **AMI**: Amazon Linux 2023
- **인스턴스 타입**: t2.micro (무료 티어)
- **키 페어**: 새로 생성
- **보안 그룹**: 다음 포트 허용
  - SSH (22)
  - HTTP (80)
  - HTTPS (443)
  - 커스텀 TCP (8000) - FastAPI용

#### 2.2 사용자 데이터 (선택사항)
```bash
#!/bin/bash
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user
```

### 3. GitHub Secrets 설정

GitHub 저장소의 Settings → Secrets and variables → Actions에서 다음 시크릿들을 설정:

#### 3.1 AWS 관련
```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-northeast-2
```

#### 3.2 EC2 관련
```
EC2_HOST=your-ec2-public-ip
SSH_PRIVATE_KEY=your-private-key-content
```

#### 3.3 데이터베이스 관련
```
DB_HOST=ai-ethics-db.xxxxx.ap-northeast-2.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=your-db-password
DB_NAME=ai_ethics_db
```

#### 3.4 애플리케이션 관련
```
SECRET_KEY=your-secret-key-here
```

### 4. 배포 프로세스

#### 4.1 자동 배포 (GitHub Actions)
1. `main` 브랜치에 코드 푸시
2. GitHub Actions가 자동으로 실행
3. 테스트 통과 후 EC2에 자동 배포

#### 4.2 수동 배포
```bash
# EC2에 SSH 연결
ssh -i your-key.pem ec2-user@your-ec2-ip

# 프로젝트 클론
git clone https://github.com/your-username/your-repo.git ai_ethics_game
cd ai_ethics_game

# 환경 변수 설정
export DB_HOST=your-rds-endpoint
export DB_PASSWORD=your-db-password
export SECRET_KEY=your-secret-key

# 배포 실행
chmod +x deploy.sh
./deploy.sh
```

### 5. 배포 확인

#### 5.1 헬스 체크
```bash
curl http://your-ec2-ip:8000/health
```

#### 5.2 API 문서
```
http://your-ec2-ip:8000/docs
```

#### 5.3 로그 확인
```bash
docker-compose logs -f
```

### 6. 환경 변수 설정

#### 6.1 프로덕션 환경 변수
```env
# Database settings
DB_HOST=ai-ethics-db.xxxxx.ap-northeast-2.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=your-strong-password
DB_NAME=ai_ethics_db

# JWT settings
SECRET_KEY=your-production-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS settings
BACKEND_CORS_ORIGINS=["https://your-frontend-domain.com"]

# Audio settings
AUDIO_UPLOAD_DIR=static/audio
MAX_AUDIO_SIZE_MB=10
```

### 7. 트러블슈팅

#### 7.1 데이터베이스 연결 오류
```bash
# RDS 보안 그룹에서 EC2 IP 허용
# EC2에서 RDS 연결 테스트
telnet your-rds-endpoint 3306
```

#### 7.2 Docker 권한 오류
```bash
# EC2에서 Docker 그룹에 사용자 추가
sudo usermod -a -G docker ec2-user
# 재로그인 필요
```

#### 7.3 포트 충돌
```bash
# 사용 중인 포트 확인
sudo netstat -tlnp | grep :8000
# 프로세스 종료
sudo kill -9 <process-id>
```

### 8. 모니터링

#### 8.1 로그 모니터링
```bash
# 실시간 로그 확인
docker-compose logs -f backend

# 특정 시간 로그 확인
docker-compose logs --since="2024-01-15T10:00:00" backend
```

#### 8.2 리소스 모니터링
```bash
# 컨테이너 상태 확인
docker-compose ps

# 리소스 사용량 확인
docker stats
```

### 9. 백업 및 복구

#### 9.1 데이터베이스 백업
```bash
# RDS 스냅샷 생성 (AWS 콘솔에서)
# 또는 mysqldump 사용
mysqldump -h your-rds-endpoint -u admin -p ai_ethics_db > backup.sql
```

#### 9.2 애플리케이션 백업
```bash
# 코드 백업
git clone https://github.com/your-username/your-repo.git

# 환경 변수 백업
cp .env .env.backup
```

### 10. 보안 고려사항

#### 10.1 네트워크 보안
- RDS 보안 그룹에서 EC2 IP만 허용
- EC2 보안 그룹에서 필요한 포트만 열기
- HTTPS 사용 권장

#### 10.2 애플리케이션 보안
- 강력한 SECRET_KEY 사용
- 환경 변수로 민감한 정보 관리
- 정기적인 보안 업데이트

#### 10.3 데이터 보안
- 정기적인 데이터베이스 백업
- 암호화된 연결 사용
- 접근 로그 모니터링

---

## 🎉 배포 완료!

배포가 완료되면 다음 URL들로 접근 가능합니다:

- **헬스 체크**: `http://your-ec2-ip:8000/health`
- **API 문서**: `http://your-ec2-ip:8000/docs`
- **OpenAPI 스키마**: `http://your-ec2-ip:8000/openapi.json`

프론트엔드에서 이 백엔드 API를 사용하여 AI 윤리게임을 구현할 수 있습니다! 