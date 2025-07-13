#!/bin/bash

# AI Ethics Game Backend 배포 스크립트

set -e

echo "🚀 AI Ethics Game Backend 배포 시작..."

# 환경 변수 확인
if [ -z "$DB_HOST" ] || [ -z "$DB_PASSWORD" ]; then
    echo "❌ 필수 환경 변수가 설정되지 않았습니다."
    exit 1
fi

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "📦 Docker 설치 중..."
    sudo yum update -y
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -a -G docker ec2-user
    echo "✅ Docker 설치 완료"
fi

# Docker Compose 설치 확인
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Docker Compose 설치 중..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose 설치 완료"
fi

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker-compose down || true
docker system prune -f

# 환경 변수 파일 생성
echo "📝 환경 변수 파일 생성 중..."
cat > .env << EOF
DB_HOST=$DB_HOST
DB_PORT=${DB_PORT:-3306}
DB_USER=${DB_USER:-admin}
DB_PASSWORD=$DB_PASSWORD
DB_NAME=${DB_NAME:-ai_ethics_db}
SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
AUDIO_UPLOAD_DIR=static/audio
MAX_AUDIO_SIZE_MB=10
EOF

# Docker Compose 실행
echo "🐳 Docker Compose 실행 중..."
docker-compose up -d --build

# 헬스 체크
echo "🏥 헬스 체크 중..."
sleep 30
for i in {1..10}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 서버가 정상적으로 실행되었습니다!"
        break
    else
        echo "⏳ 서버 시작 대기 중... ($i/10)"
        sleep 10
    fi
done

if [ $i -eq 10 ]; then
    echo "❌ 서버 시작 실패"
    docker-compose logs
    exit 1
fi

echo "🎉 배포가 완료되었습니다!"
echo "📊 서버 상태: http://localhost:8000/health"
echo "📚 API 문서: http://localhost:8000/docs" 