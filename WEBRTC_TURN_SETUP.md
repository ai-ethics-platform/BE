# WebRTC TURN 서버 설정 가이드

## 🎯 목적

특정 네트워크 환경(NAT, 방화벽, VPN, 대칭 NAT 등)에서 WebRTC P2P 연결이 실패하는 문제를 해결하기 위해 **Twilio TURN 서버**를 추가합니다.

## 🔍 문제 증상

```
✅ 시그널링 성공 (offer/answer 교환)
❌ ICE 연결 실패 (iceConnectionState: disconnected/failed)
→ 음성이 연결되지 않음
```

## ✅ 해결 방법

### 1단계: Twilio 계정 설정

1. **Twilio 계정 생성**
   - https://www.twilio.com/console 접속
   - 회원가입 (무료 체험 가능)

2. **API 키 확인**
   - Dashboard → Account → Keys & Credentials
   - `Account SID` 복사
   - `Auth Token` 복사

### 2단계: 백엔드 환경변수 설정

`.env` 파일에 다음 추가:

```bash
# Twilio TURN 서버 설정
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_ICE_TTL_SECONDS=3600  # 선택사항, 기본 1시간
```

### 3단계: 서버 재시작

```bash
# Docker 사용 시
docker-compose down
docker-compose build
docker-compose up -d

# 로컬 개발 시
# requirements.txt 이미 httpx 포함되어 있음
uvicorn app.main:app --reload
```

## 📡 API 사용법

### 엔드포인트

```
GET /webrtc/ice-config?token={JWT_TOKEN}
```

### 응답 예시

**Twilio 설정 O (TURN 포함):**
```json
{
  "iceServers": [
    {
      "urls": "stun:global.stun.twilio.com:3478"
    },
    {
      "urls": "turn:global.turn.twilio.com:3478?transport=udp",
      "username": "xxxxxxxxx",
      "credential": "xxxxxxxxx"
    },
    {
      "urls": "turn:global.turn.twilio.com:3478?transport=tcp",
      "username": "xxxxxxxxx",
      "credential": "xxxxxxxxx"
    }
  ],
  "ttl": 3600,
  "turnEnabled": true
}
```

**Twilio 설정 X (기본 STUN만):**
```json
{
  "iceServers": [
    {
      "urls": "stun:stun.l.google.com:19302"
    },
    {
      "urls": "stun:stun1.l.google.com:19302"
    }
  ],
  "ttl": 3600,
  "turnEnabled": false
}
```

## 🎨 프론트엔드 연동

### 1. ICE 서버 설정 가져오기

```typescript
// WebRTC 시작 전에 호출
async function getIceServers(token: string) {
  const response = await fetch(
    `https://your-domain.com/webrtc/ice-config?token=${token}`
  );
  
  if (!response.ok) {
    console.warn("ICE config 조회 실패, 기본 STUN 사용");
    return {
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
    };
  }
  
  const data = await response.json();
  return data;
}
```

### 2. RTCPeerConnection 생성 시 사용

```typescript
// 기존 코드
const peerConnection = new RTCPeerConnection({
  iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
});

// ↓ 변경
const iceConfig = await getIceServers(accessToken);
const peerConnection = new RTCPeerConnection({
  iceServers: iceConfig.iceServers
});
```

### 3. 디버깅

```javascript
peerConnection.onicecandidate = (event) => {
  if (event.candidate) {
    console.log("ICE Candidate:", event.candidate.type);
    // relay = TURN 경유 성공
    // srflx = STUN 성공 (P2P)
    // host = 로컬
  }
};

peerConnection.oniceconnectionstatechange = () => {
  console.log("ICE State:", peerConnection.iceConnectionState);
  // connected = 성공
  // failed = 실패 (TURN이 필요)
};
```

## 🔧 헬스 체크

```bash
curl https://your-domain.com/webrtc/health
```

**응답:**
```json
{
  "status": "healthy",
  "turn_configured": true,
  "message": "WebRTC ICE config service is running"
}
```

## 💰 Twilio 비용

### 무료 크레딧
- 신규 가입 시 **$15 무료 크레딧**
- Network Traversal Service 무료 사용

### 유료 전환 후
- **STUN**: 무료
- **TURN**: 약 $0.0005/분/연결
  - 예: 100명이 동시에 1시간 음성 통화 = 약 $3

> 대부분의 연결은 STUN(무료)으로 성공하고, TURN은 특수 환경에서만 사용됩니다.

## 🐛 문제 해결

### 1. "Twilio API error: 401"
→ `TWILIO_ACCOUNT_SID` 또는 `TWILIO_AUTH_TOKEN`이 잘못됨

### 2. "Twilio API timeout"
→ 서버에서 Twilio API 접근 불가 (방화벽 확인)

### 3. 여전히 연결 실패
→ 프론트엔드 콘솔에서 확인:
```javascript
// relay candidate가 있는지 확인
peerConnection.onicecandidate = (e) => {
  console.log(e.candidate?.type); // "relay"가 있어야 함
}
```

## 📊 모니터링

Twilio Console에서 실시간 확인:
- https://www.twilio.com/console/voice/calls/logs
- Network Traversal 사용량
- 비용 트래킹


## 📝 참고

- Twilio Network Traversal: https://www.twilio.com/docs/stun-turn
- WebRTC ICE: https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection
- TURN 서버 필요성: https://bloggeek.me/webrtc-turn/
