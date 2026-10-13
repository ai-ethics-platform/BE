import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from app import models, schemas
from app.services.room_service import RoomService


class RoomGameBindingTests(unittest.IsolatedAsyncioTestCase):
    async def test_public_and_private_rooms_store_validated_game_code(self):
        for method, schema in [(RoomService.create_public_room, schemas.RoomCreatePublic),
                               (RoomService.create_private_room, schemas.RoomCreatePrivate)]:
            for code in ['CUSTOM_GAME', None]:
                added = []
                db = SimpleNamespace(add=added.append, flush=AsyncMock(), commit=AsyncMock(), refresh=AsyncMock())
                result = SimpleNamespace(scalar_one_or_none=lambda: 1, scalar_one=lambda: added[0])
                db.execute = AsyncMock(return_value=result)
                payload = schema(title='수업', topic='수업', custom_game_code=code)
                with patch.object(RoomService, '_generate_unique_room_code', AsyncMock(return_value='123456')):
                    room = await method(db, payload, 1, 'test-player')
                self.assertIsInstance(room, models.Room)
                self.assertEqual(room.custom_game_code, code)
                self.assertEqual(room.room_code, '123456')

    async def test_invalid_game_is_rejected_before_room_creation(self):
        db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None)), add=Mock())
        with self.assertRaisesRegex(ValueError, '존재하지 않는 커스텀'):
            await RoomService.create_private_room(db, schemas.RoomCreatePrivate(title='수업', topic='수업', custom_game_code='MISSING'), 1, 'test')
        db.add.assert_not_called()

    async def test_missing_or_different_game_cannot_ready(self):
        room = SimpleNamespace(custom_game_code='CUSTOM_GAME')
        for code in [None, 'OTHER_GAME']:
            db = SimpleNamespace(execute=AsyncMock(), commit=AsyncMock())
            with patch.object(RoomService, 'get_room_by_code', AsyncMock(return_value=room)):
                with self.assertRaisesRegex(ValueError, '먼저 불러와야'):
                    await RoomService.toggle_ready_status(db, '123456', 1, None, code)
            db.execute.assert_not_called()
            db.commit.assert_not_called()

    async def test_three_matching_players_start_and_can_cancel(self):
        participants = [SimpleNamespace(is_ready=False) for _ in range(3)]
        room = SimpleNamespace(id=1, custom_game_code='CUSTOM_GAME', is_active=True, is_started=False)
        with patch.object(RoomService, 'get_room_by_code', AsyncMock(return_value=room)):
            for index in [0, 1, 2, 2]:
                result = SimpleNamespace(scalar_one_or_none=lambda: participants[index],
                                         scalars=lambda: SimpleNamespace(all=lambda: participants))
                db = SimpleNamespace(execute=AsyncMock(return_value=result), commit=AsyncMock(), refresh=AsyncMock())
                _, _, starting, _ = await RoomService.toggle_ready_status(db, '123456', index + 1, None, 'CUSTOM_GAME')
                self.assertEqual(starting, all(p.is_ready for p in participants))
            self.assertFalse(participants[2].is_ready)

    async def test_basic_room_still_accepts_ready_without_custom_code(self):
        room = SimpleNamespace(id=1, custom_game_code=None, is_active=True, is_started=False)
        participant = SimpleNamespace(is_ready=False)
        result = SimpleNamespace(scalar_one_or_none=lambda: participant,
                                 scalars=lambda: SimpleNamespace(all=lambda: [participant]))
        db = SimpleNamespace(execute=AsyncMock(return_value=result), commit=AsyncMock(), refresh=AsyncMock())
        with patch.object(RoomService, 'get_room_by_code', AsyncMock(return_value=room)):
            _, _, starting, _ = await RoomService.toggle_ready_status(db, '123456', 1, None)
        self.assertTrue(participant.is_ready)
        self.assertFalse(starting)

    def test_migration_keeps_existing_rooms(self):
        path = Path(__file__).parents[1] / 'alembic/versions/7c02822b96af_bind_rooms_to_custom_games.py'
        spec = importlib.util.spec_from_file_location('room_game_migration', path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        with sa.create_engine('sqlite://').begin() as connection:
            connection.execute(sa.text('CREATE TABLE rooms (id INTEGER PRIMARY KEY, title VARCHAR(100))'))
            connection.execute(sa.text("INSERT INTO rooms VALUES (1, 'existing room')"))
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                self.assertEqual(connection.execute(sa.text('SELECT title, custom_game_code FROM rooms')).one(), ('existing room', None))
                migration.downgrade()
                self.assertEqual(connection.execute(sa.text('SELECT title FROM rooms')).scalar_one(), 'existing room')


if __name__ == '__main__':
    unittest.main()
