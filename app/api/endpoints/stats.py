from typing import Any, Dict, List, Set

from fastapi import APIRouter, HTTPException

from app.core.websocket_manager import websocket_manager
from app.api.voice_signaling_ws import manager as signaling_manager


router = APIRouter()


@router.get("/voice/sessions")
async def list_voice_sessions(active_only: bool = False) -> Any:
    """현재 서버의 음성 세션 요약 통계 목록."""
    all_stats: Dict[str, dict] = websocket_manager.get_all_stats()
    sessions: List[dict] = []
    for session_id, stats in all_stats.items():
        if active_only and stats.get("current_connections", 0) <= 0:
            continue
        sessions.append({
            "session_id": session_id,
            **stats,
        })
    return {"sessions": sessions, "count": len(sessions)}


@router.get("/voice/sessions/{session_id}")
async def get_voice_session_detail(session_id: str) -> Any:
    """특정 음성 세션의 상세 통계와 연결 정보."""
    stats = websocket_manager.get_connection_stats(session_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Session not found")

    # 연결 상세 수집
    connections: List[dict] = []
    for ws, info in list(websocket_manager.connection_info.items()):
        if info.get("session_id") == session_id:
            connections.append({
                "connection_id": str(id(ws)),
                "connected_at": info.get("connected_at"),
                "last_heartbeat": info.get("last_heartbeat"),
                "user_info": info.get("user_info", {}),
            })

    return {
        "session_id": session_id,
        "stats": stats,
        "connections": connections,
    }


@router.get("/voice/sessions/{session_id}/health")
async def get_voice_session_health(session_id: str) -> Any:
    """세션 내 각 연결의 헬스 상태."""
    health = websocket_manager.get_connection_health(session_id)
    return {"session_id": session_id, "health": health}


@router.post("/voice/sessions/{session_id}/ping")
async def ping_voice_session(session_id: str) -> Any:
    """세션 내 연결들에게 ping 전송 트리거."""
    await websocket_manager.ping_connections(session_id)
    return {"session_id": session_id, "status": "ping_sent"}


@router.get("/signaling/rooms")
async def list_signaling_rooms() -> Any:
    """시그널링 방들의 현재 연결/피어 요약."""
    room_codes: Set[str] = set(signaling_manager.active_connections.keys()) | set(signaling_manager.room_peers.keys())
    rooms: List[dict] = []
    for room_code in sorted(room_codes):
        current_connections = len(signaling_manager.active_connections.get(room_code, []))
        peers = list(signaling_manager.room_peers.get(room_code, {}).keys())
        rooms.append({
            "room_code": room_code,
            "current_connections": current_connections,
            "peers": peers,
        })
    return {"rooms": rooms, "count": len(rooms)}


@router.get("/signaling/rooms/{room_code}")
async def get_signaling_room(room_code: str) -> Any:
    """특정 시그널링 방의 상세."""
    current_connections = len(signaling_manager.active_connections.get(room_code, []))
    peers_map = signaling_manager.room_peers.get(room_code)
    if current_connections == 0 and not peers_map:
        raise HTTPException(status_code=404, detail="Room not found")
    peers = list(peers_map.keys()) if peers_map else []
    return {
        "room_code": room_code,
        "current_connections": current_connections,
        "peers": [{"peer_id": pid} for pid in peers],
    }


