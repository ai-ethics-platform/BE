#!/bin/bash

# SSL 인증서 만료 확인 스크립트
DOMAIN="dilemmai.org"
ALERT_DAYS=30  # 만료 30일 전 알림

# 인증서 만료일 확인
get_cert_expiry() {
    local domain=$1
    echo | openssl s_client -connect $domain:443 -servername $domain 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2
}

# 날짜 차이 계산 (일 단위)
get_days_until_expiry() {
    local expiry_date=$1
    local expiry_timestamp=$(date -d "$expiry_date" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$expiry_date" +%s 2>/dev/null)
    local current_timestamp=$(date +%s)
    echo $(( (expiry_timestamp - current_timestamp) / 86400 ))
}

# 메인 로직
expiry_date=$(get_cert_expiry $DOMAIN)
days_until_expiry=$(get_days_until_expiry "$expiry_date")

echo "도메인: $DOMAIN"
echo "만료일: $expiry_date"
echo "만료까지 남은 일수: $days_until_expiry"

if [ $days_until_expiry -lt $ALERT_DAYS ]; then
    echo "⚠️  경고: SSL 인증서가 $days_until_expiry 일 후 만료됩니다!"
    echo "인증서 갱신을 진행하세요:"
    echo "sudo certbot renew"
    exit 1
else
    echo "✅ SSL 인증서가 정상적으로 유효합니다."
    exit 0
fi

