"""
WebRTC ICE 서버 설정 API
Twilio TURN 서버를 통한 NAT/방화벽 우회 지원
"""
import os
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, Query, HTTPException, status, Depends

from app.core.security import verify_token
from app.core.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _normalize_twilio_ice_servers(twilio_ice_servers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Twilio ICE 서버 응답을 브라우저 표준 형식으로 변환
    
    Twilio는 url 또는 urls로 반환할 수 있으므로 정규화
    """
    normalized: List[Dict[str, Any]] = []
    
    for server in twilio_ice_servers or []:
        # Twilio는 url 또는 urls로 올 수 있음
        urls = server.get("urls")
        if not urls:
            url = server.get("url")
            if url:
                urls = [url] if isinstance(url, str) else url
        
        if not urls:
            continue

        item: Dict[str, Any] = {"urls": urls}
        
        # TURN 서버는 인증 정보 필요
        if "username" in server:
            item["username"] = server["username"]
        if "credential" in server:
            item["credential"] = server["credential"]
        
        normalized.append(item)
    
    return normalized


@router.get("/ice-config")
async def get_ice_config(
    token: str = Query(..., description="JWT 인증 토큰"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    WebRTC ICE 서버 설정 조회
    
    Twilio TURN 서버를 사용하여 NAT/방화벽 환경에서도
    안정적인 P2P 연결을 지원합니다.
    
    Returns:
        {
            "iceServers": [...],
            "ttl": 3600,
            "turnEnabled": true
        }
    """
    # 1. 토큰 검증
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # 2. Twilio 설정 확인
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    ttl = int(os.getenv("TWILIO_ICE_TTL_SECONDS", "3600"))  # 기본 1시간
    
    # Twilio 설정이 없으면 기본 STUN만 반환
    if not account_sid or not auth_token:
        print("⚠️  Twilio 설정 없음 - 기본 STUN만 사용")
        return {
            "iceServers": [
                {"urls": "stun:stun.l.google.com:19302"},
                {"urls": "stun:stun1.l.google.com:19302"}
            ],
            "ttl": ttl,
            "turnEnabled": False
        }
    
    # 3. Twilio Network Traversal Service 호출
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Tokens.json"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                auth=(account_sid, auth_token),  # HTTP Basic Auth
                data={"Ttl": str(ttl)},
            )
            
            if response.status_code >= 400:
                print(f"❌ Twilio API 오류: {response.status_code} {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Twilio API error: {response.status_code}"
                )
            
            data = response.json()
            
    except httpx.TimeoutException:
        print("❌ Twilio API 타임아웃")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Twilio API timeout"
        )
    except httpx.HTTPError as e:
        print(f"❌ Twilio API 연결 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Twilio: {str(e)}"
        )
    
    # 4. ICE 서버 정규화
    twilio_ice = data.get("ice_servers") or data.get("iceServers") or []
    ice_servers = _normalize_twilio_ice_servers(twilio_ice)
    
    # 5. Google STUN을 백업으로 추가 (Twilio가 이미 포함할 수도 있음)
    if not any("stun" in str(server.get("urls", "")).lower() for server in ice_servers):
        ice_servers.insert(0, {"urls": "stun:stun.l.google.com:19302"})
    
    print(f"✅ ICE 서버 설정 발급 성공 (TURN 포함: {len(ice_servers)}개)")
    
    return {
        "iceServers": ice_servers,
        "ttl": ttl,
        "turnEnabled": True
    }


@router.get("/health")
async def webrtc_health_check() -> Dict[str, Any]:
    """
    WebRTC 서비스 헬스 체크
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    
    return {
        "status": "healthy",
        "turn_configured": bool(account_sid and auth_token),
        "message": "WebRTC ICE config service is running"
    }
