# AI Ethics Game Backend 배포 가이드

## 🚀 배포 아키텍처

```
Internet → Nginx (SSL/TLS) → FastAPI Backend → PostgreSQL + Redis
```

## 📋 사전 요구사항

### 서버 요구사항
- Ubuntu 20.04+ 또는 CentOS 8+
- Docker & Docker Compose
- 최소 2GB RAM, 20GB 디스크
- 도메인 (SSL 인증서용)

### GitHub Secrets 설정
다음 시크릿을 GitHub 저장소에 설정해야 합니다:

1. **DOCKER_USERNAME**: Docker Hub 사용자명
2. **DOCKER_PASSWORD**: Docker Hub 액세스 토큰
3. **SERVER_HOST**: 서버 IP 주소
4. **SERVER_USERNAME**: 서버 SSH 사용자명
5. **SERVER_SSH_KEY**: 서버 SSH 개인키

## 🔧 서버 초기 설정

### 1. Docker 설치
```bash
# Ubuntu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 프로젝트 디렉토리 생성
```bash
sudo mkdir -p /opt/ai-ethics-game
sudo chown $USER:$USER /opt/ai-ethics-game
cd /opt/ai-ethics-game
```

### 3. SSL 인증서 설정 (Let's Encrypt)
```bash
# Certbot 설치
sudo apt install certbot

# SSL 인증서 발급
sudo certbot certonly --standalone -d your-domain.com

# 인증서를 Nginx용 디렉토리로 복사
sudo mkdir -p /opt/ai-ethics-game/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/ai-ethics-game/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/ai-ethics-game/ssl/key.pem
sudo chown -R $USER:$USER /opt/ai-ethics-game/ssl
```

## 🚀 배포 방법

### 방법 1: GitHub Actions 자동 배포 (권장)

1. **GitHub 저장소에 코드 푸시**
   ```bash
   git add .
   git commit -m "Add deployment configuration"
   git push origin main
   ```

2. **GitHub Actions에서 자동 배포 확인**
   - GitHub 저장소 → Actions 탭에서 배포 진행 상황 확인

### 방법 2: 수동 배포

1. **서버에 프로젝트 파일 복사**
   ```bash
   scp -r . user@your-server:/opt/ai-ethics-game/
   ```

2. **환경 변수 설정**
   ```bash
   cd /opt/ai-ethics-game
   cp .env.example .env
   # .env 파일 편집하여 실제 값으로 설정
   ```

3. **배포 실행**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

## 🔧 환경 변수 설정

`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
# 데이터베이스
DATABASE_URL=postgresql+asyncpg://ai_ethics_user:ai_ethics_password@postgres:5432/ai_ethics_db

# Redis
REDIS_URL=redis://redis:6379

# JWT
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# CORS
BACKEND_CORS_ORIGINS=["https://your-domain.com", "http://localhost:3000"]

# 도메인
DOMAIN=your-domain.com
```

## 📊 모니터링 및 로그

### 서비스 상태 확인
```bash
# 모든 서비스 상태 확인
docker-compose ps

# 특정 서비스 로그 확인
docker-compose logs backend
docker-compose logs nginx
docker-compose logs postgres
```

### 헬스 체크
```bash
# 백엔드 헬스 체크
curl http://localhost:8000/health

# Nginx를 통한 헬스 체크
curl https://your-domain.com/health
```

## 🔄 업데이트 및 롤백

### 업데이트
```bash
cd /opt/ai-ethics-game
git pull origin main
./deploy.sh
```

### 롤백
```bash
# 이전 이미지로 롤백
docker-compose down
docker-compose up -d backend:previous-tag
```

## 🛠️ 문제 해결

### 일반적인 문제들

1. **포트 충돌**
   ```bash
   # 사용 중인 포트 확인
   sudo netstat -tulpn | grep :80
   sudo netstat -tulpn | grep :443
   ```

2. **권한 문제**
   ```bash
   # Docker 권한 확인
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **SSL 인증서 갱신**
   ```bash
   # Let's Encrypt 인증서 자동 갱신
   sudo crontab -e
   # 다음 줄 추가: 0 12 * * * /usr/bin/certbot renew --quiet
   ```

### 로그 확인
```bash
# 실시간 로그 확인
docker-compose logs -f backend

# 특정 시간 이후 로그
docker-compose logs --since="2024-01-01T00:00:00" backend
```

## 📈 성능 최적화

### Nginx 설정 최적화
- Gzip 압축 활성화
- 정적 파일 캐싱
- HTTP/2 지원

### 데이터베이스 최적화
- PostgreSQL 설정 튜닝
- 인덱스 최적화
- 연결 풀 설정

## 🔒 보안 설정

### 방화벽 설정
```bash
# UFW 방화벽 설정
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### SSL/TLS 보안
- HSTS 헤더 설정
- 보안 헤더 추가
- SSL 프로토콜 제한

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. 서비스 로그: `docker-compose logs`
2. 시스템 리소스: `htop`, `df -h`
3. 네트워크 연결: `ping`, `curl` 