"""Record server-received gameplay request context without request bodies."""
import asyncio
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from jose import jwt

from app.core.config import settings
from app.core.error_tracking import capture_event

logger = logging.getLogger(__name__)
pending = set()
CODE = re.compile(r"^[\w-]{1,20}$", re.ASCII)
TRACKED = re.compile(r"^/(?:auth/login(?:-json)?|custom-games/[^/]+|rooms/(?:join(?:/[^/]+)?|ready|create/(?:public|private)|page-arrival))$")


def context_from_headers(headers):
    raw = headers.get('x-game-context', '')
    if not raw:
        return {'context_status': 'missing'}
    try:
        if len(raw) > 1500:
            raise ValueError()
        values = json.loads(raw)
        if not isinstance(values, dict) or values.get('version') != 1:
            raise ValueError()
        result = {'context_status': 'received'}
        for key in ('url_code', 'game_code', 'loaded_code', 'room_code'):
            value = values.get(key)
            result[key] = value if isinstance(value, str) and CODE.fullmatch(value) else None
        for key, pattern, limit in [('path', r'^/[\w/-]*$', 100), ('page_id', r'^[\w-]+$', 80), ('build_id', r'^[\w.-]*$', 100)]:
            value = values.get(key, '')
            result[key] = value if isinstance(value, str) and len(value) <= limit and re.fullmatch(pattern, value, re.ASCII) else ''
        result['storage_state'] = values.get('storage_state') if values.get('storage_state') in ('available', 'unavailable') else 'unknown'
        result['role_id'] = values.get('role_id') if type(values.get('role_id')) is int and values['role_id'] in (1, 2, 3) else None
        return result
    except (ValueError, TypeError):
        return {'context_status': 'invalid'}


def record_request(request, status):
    if request.method == 'OPTIONS' or not TRACKED.fullmatch(request.url.path):
        return
    context = context_from_headers(request.headers)
    if hasattr(request.state, 'diagnostic_room_code'):
        context['room_code'] = request.state.diagnostic_room_code
    for name in ('submitted_game_code', 'room_game_code'):
        value = getattr(request.state, f'diagnostic_{name}', None)
        context[name] = value if isinstance(value, str) and CODE.fullmatch(value) else None
    context['submitted_game_code_recorded'] = hasattr(request.state, 'diagnostic_submitted_game_code')
    user_id = getattr(request.state, 'diagnostic_user_id', None)
    if user_id is None:
        # Verify the claim for correlation only; this never authorizes a request.
        try:
            scheme, token = request.headers.get('authorization', '').split(' ', 1)
            if scheme.lower() == 'bearer':
                user_id = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256']).get('sub')
        except Exception:
            pass
    actor = hashlib.sha256(f'game-account:{user_id}'.encode()).hexdigest()[:16] if user_id is not None else ''
    requested_code = request.path_params.get('code')
    context['requested_game_code'] = requested_code if isinstance(requested_code, str) and CODE.fullmatch(requested_code) else None
    route = getattr(request.scope.get('route'), 'path', '/unknown')
    payload = {'request_id': str(uuid4()), 'at': datetime.now(timezone.utc).isoformat(),
               'endpoint': route, 'method': request.method, 'status': status,
               'account_ref': actor, **context}
    capture_event('game_api_request', payload, request.headers.get('x-posthog-session-id'))
    if os.getenv('GAME_DIAGNOSTIC_URL') and os.getenv('GAME_DIAGNOSTIC_API_KEY'):
        if len(pending) >= 100:
            logger.warning('Game diagnostic backlog full; request_id=%s', payload['request_id'])
            return
        task = asyncio.create_task(send_to_admin(payload))
        pending.add(task)
        task.add_done_callback(pending.discard)


async def send_to_admin(payload):
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            for attempt in range(2):
                try:
                    response = await client.post(os.environ['GAME_DIAGNOSTIC_URL'], json=payload,
                        headers={'x-game-diagnostic-key': os.environ['GAME_DIAGNOSTIC_API_KEY']})
                    response.raise_for_status()
                    return
                except httpx.HTTPError:
                    if attempt:
                        raise
    except Exception:
        logger.warning('Game request diagnostic delivery failed; request_id=%s', payload['request_id'])


async def flush_game_diagnostics():
    if pending:
        await asyncio.wait(list(pending), timeout=9)
