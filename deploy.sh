#!/bin/bash

# AI Ethics Game Backend 배포 스크립트

set -e

echo "🚀 AI Ethics Game Backend 배포 시작..."

# 환경 변수 설정
export COMPOSE_PROJECT_NAME=ai_ethics_game

# 기존 컨테이너 중지 및 제거
echo "📦 기존 컨테이너 정리..."
docker-compose down --remove-orphans

# 최신 이미지 가져오기
echo "🔄 최신 이미지 가져오기..."
docker-compose pull

# 새 컨테이너 시작
echo "🚀 새 컨테이너 시작..."
docker-compose up -d

# 헬스 체크
echo "🏥 헬스 체크..."
sleep 10

# 백엔드 서비스 상태 확인
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 백엔드 서비스가 정상적으로 실행되었습니다."
else
    echo "❌ 백엔드 서비스 실행에 실패했습니다."
    docker-compose logs backend
    exit 1
fi

# 불필요한 Docker 리소스 정리
echo "🧹 불필요한 Docker 리소스 정리..."
docker system prune -f

echo "🎉 배포가 완료되었습니다!"
echo "📊 서비스 상태:"
docker-compose ps 