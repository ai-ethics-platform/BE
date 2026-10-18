"""Browser-reported state, authenticated at receipt and kept distinct from API evidence."""
import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.core.deps import get_current_user_or_guest, get_db
from app.core.game_diagnostics import context_from_headers, send_to_admin
from app.schemas.game_diagnostic import BrowserGameBatch

router = APIRouter()


@router.post('/game-diagnostics')
async def receive_game_diagnostics(request: Request, db: AsyncSession = Depends(get_db),
                                   user=Depends(get_current_user_or_guest)):
    if user is None:
        raise HTTPException(401, 'Authentication required')
    if not os.getenv('GAME_DIAGNOSTIC_URL') or not os.getenv('GAME_DIAGNOSTIC_API_KEY'):
        raise HTTPException(503, 'Diagnostics unavailable')
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 20000:
            raise HTTPException(413, 'Diagnostic batch too large')
    try:
        batch = BrowserGameBatch.model_validate_json(body)
    except ValidationError:
        raise HTTPException(400, 'Invalid diagnostic batch')
    identity = f"guest:{user.get('guest_id')}" if isinstance(user, dict) else user.id
    actor = hashlib.sha256(f'game-account:{identity}'.encode()).hexdigest()[:16]
    room_codes = {}
    payloads = []
    for item in batch.events:
        context = context_from_headers({'x-game-context': json.dumps(item.context)})
        room_code = context.get('room_code')
        if room_code and room_code not in room_codes:
            room_codes[room_code] = (await db.execute(select(models.Room.custom_game_code)
                .where(models.Room.room_code == room_code))).scalar_one_or_none()
        payloads.append({
            'request_id': str(item.id), 'at': datetime.now(timezone.utc).isoformat(),
            'endpoint': '/game-diagnostics', 'method': 'POST', 'status': 200,
            'account_ref': actor, **context, 'room_game_code': room_codes.get(room_code),
            'event': item.event, 'client_at': item.at.isoformat(), 'sequence': item.sequence,
            'details': item.details, 'evidence_source': 'browser_report',
        })
    # This separate diagnostic request acknowledges only after the admin DB accepts every event.
    delivered = await asyncio.gather(*(send_to_admin(payload) for payload in payloads))
    if not all(delivered):
        raise HTTPException(503, 'Diagnostic delivery incomplete')
    return {'ok': True}
