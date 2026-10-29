"""Preview access checks with an in-memory game; no database or AI calls."""
import importlib
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI


@pytest.mark.asyncio
async def test_preview_requires_private_edit_code(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SECRET_KEY", "offline-test-only")
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-only")
    deps = ModuleType("app.core.deps")
    deps.get_db = lambda: None
    monkeypatch.setitem(sys.modules, "app.core.deps", deps)
    module = importlib.import_module("app.api.endpoints.custom_games")
    game = SimpleNamespace(code="public-game", edit_code="private-teacher-code", title="테스트 게임",
                           representative_image_url=None, teacher_email="private@example.test",
                           data=json.dumps({"opening": ["이야기"], "roles": []}))
    lookup = AsyncMock(return_value=game)
    monkeypatch.setattr(module.custom_game_service, "get_by_code", lookup)
    app = FastAPI()
    app.include_router(module.router)
    app.dependency_overrides[module.get_db] = lambda: None
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        url = "/custom-games/public-game/preview"
        assert (await client.get(url)).status_code == 422
        assert (await client.get(url, headers={"X-Edit-Code": "public-game"})).status_code == 403
        assert (await client.get(url, headers={"X-Edit-Code": "wrong"})).status_code == 403
        assert (await client.get(url, headers={"X-Edit-Code": ""})).status_code == 422
        response = await client.get(url, headers={"X-Edit-Code": "private-teacher-code"})
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.json() == {"code": "public-game", "title": "테스트 게임", "representative_image_url": None,
                                   "data": {"opening": ["이야기"], "roles": []}}
        assert isinstance(game.data, str), "Reading a preview must not mutate the stored game"
        game.edit_code = None
        assert (await client.get(url, headers={"X-Edit-Code": "wrong"})).status_code == 403
        assert not module.custom_game_service.verify_edit_code(game, "")
        lookup.return_value = None
        assert (await client.get(url, headers={"X-Edit-Code": "private-teacher-code"})).status_code == 404


def test_edit_code_migration_round_trip():
    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    path = Path(__file__).resolve().parents[1] / 'alembic/versions/c7d8e9f0a1b2_add_custom_game_edit_code.py'
    spec = importlib.util.spec_from_file_location('preview_migration', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with sa.create_engine('sqlite://').begin() as connection:
        connection.execute(sa.text('CREATE TABLE custom_games (id INTEGER PRIMARY KEY)'))
        connection.execute(sa.text('INSERT INTO custom_games (id) VALUES (1)'))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            assert connection.execute(sa.text('SELECT edit_code FROM custom_games WHERE id = 1')).scalar() is None
            assert sa.inspect(connection).get_indexes('custom_games')[0]['unique']
            migration.downgrade()
            assert [column['name'] for column in sa.inspect(connection).get_columns('custom_games')] == ['id']
