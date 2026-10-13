# SSL Renewal Runbook (dilemmai)

이 문서는 `dilemmai-idl.com` 서비스의 Let's Encrypt 인증서 운영/갱신을 위한 인수인계 문서입니다.

## 1) 현재 운영 상태 요약

- 인증서 공급자: Let's Encrypt
- 웹서버: Nginx (Docker 컨테이너)
- 인증서 경로(nginx 설정 기준):
  - `/etc/letsencrypt/live/www.dilemmai-idl.com/fullchain.pem`
  - `/etc/letsencrypt/live/www.dilemmai-idl.com/privkey.pem`
- 인증서 자동 갱신: **미구성(수동 갱신 필요)**

주의:
- 실제 운영 도메인을 먼저 확정한 뒤, nginx 설정/인증서 발급 대상을 일치시켜야 합니다.

## 2) 관련 설정 위치

- Nginx SSL 설정: `nginx.conf`
  - HTTPS listen/server_name
  - `ssl_certificate`
  - `ssl_certificate_key`
- Docker 볼륨 마운트: `docker-compose.yml`
  - `/etc/letsencrypt:/etc/letsencrypt`
  - `./certbot:/var/www/certbot`
- 만료 점검 스크립트: `check_ssl_expiry.sh`

## 3) 서버 접속 정보(관리 포인트)

보안상 이 저장소에는 실제 접속값을 두지 않습니다. 아래 위치에서 확인합니다.

- EC2 주소/계정/키:
  - GitHub Actions 시크릿: `EC2_HOST`, `EC2_USER`, `EC2_KEY`
  - 참조 파일: `.github/workflows/deploy.yml`
- 실제 운영 접근 권한:
  - AWS 계정 내 EC2 인스턴스/보안그룹
  - SSH 키 파일 보관 위치(조직 보안 정책 위치)

## 4) 인증서 수동 갱신 절차(표준)

1. 운영 서버 접속
   - `ssh -i <key.pem> <user>@<host>`
2. 현재 인증서 확인
   - `sudo certbot certificates`
3. 사전 테스트(dry-run)
   - `sudo certbot renew --dry-run`
4. 실제 갱신
   - `sudo certbot renew`
5. Nginx 설정 검증 및 재적용
   - `sudo nginx -t`
   - `sudo systemctl reload nginx`
6. 외부 만료일 확인
   - `echo | openssl s_client -connect www.dilemmai-idl.com:443 -servername www.dilemmai-idl.com 2>/dev/null | openssl x509 -noout -enddate`

성공 기준:
- `certbot renew` 실패 없음
- `nginx -t` OK
- 외부에서 확인한 만료일이 갱신됨

## 5) 자동 갱신 미동작/실패의 대표 원인

- 서버에 `certbot.timer` 또는 cron 미구성
- 도메인/인증서 경로 불일치
- ACME challenge 경로(`/.well-known/acme-challenge/`) 라우팅 불일치
- 80/443 포트 접근 불가(보안그룹/방화벽)
- 갱신 후 nginx reload 누락

## 6) 권장 자동화 방식

### 옵션 A: host certbot + systemd timer (권장)

운영 서버 host OS에 certbot 설치 후 timer 사용:

- 상태 확인:
  - `systemctl status certbot.timer`
  - `systemctl list-timers | grep certbot`
- 활성화:
  - `sudo systemctl enable --now certbot.timer`
- 훅(갱신 후 nginx reload):
  - `/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh`

예시 스크립트:
```bash
#!/usr/bin/env bash
set -euo pipefail
nginx -t
systemctl reload nginx
```

### 옵션 B: cron 기반

하루 2회 정도 renew 점검:

```cron
0 3,15 * * * /usr/bin/certbot renew --quiet --deploy-hook "nginx -t && systemctl reload nginx"
```

## 7) 장애 대응(트러블슈팅)

- certbot 실패 로그:
  - `/var/log/letsencrypt/letsencrypt.log`
- nginx 오류 로그:
  - `/var/log/nginx/error.log`
- 즉시 점검 명령:
  - `sudo certbot certificates`
  - `sudo certbot renew --dry-run`
  - `sudo nginx -t`
  - `sudo ss -tulpen | grep -E ':80|:443'`

증상별 가이드:
- ACME 인증 실패: DNS A 레코드/도메인 대상 서버 확인
- challenge 404: nginx `/.well-known/acme-challenge/` 경로와 webroot 일치 여부 확인
- reload 실패: nginx 설정 문법/인증서 경로 오타 점검

## 8) 운영 시 유의사항

- 인증서 파일/개인키를 Git에 커밋하지 말 것
- 도메인 표기를 단일 기준으로 통일할 것
- 배포 전후로 인증서 만료일/체인 상태를 정기 확인할 것
- 인수인계 시 다음 항목을 반드시 함께 전달할 것:
  - 실제 운영 도메인 목록
  - 발급 방식(webroot/nginx)과 발급 명령
  - 자동화(cron/timer) 설정 위치
  - 실패 로그 확인 위치
  - 비상시 수동 갱신 절차

## 9) 권장 후속 작업(문서/설정 정합성)

- `PORTFOLIO.md`, `PORTFOLIO_NOTION.md`, `nginx.conf`의 도메인 표기 통일
- 실제 운영 방식 확정 후 문서의 "자동 갱신" 문구 업데이트
- 자동화 구성 완료 시 이 문서에 점검 명령 결과 스냅샷 추가
