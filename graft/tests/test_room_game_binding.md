# tests/test_room_game_binding.py

- RoomGameBindingTests · class · L14-L81 — class RoomGameBindingTests(unittest.IsolatedAsyncioTestCase)
- test_public_and_private_rooms_store_validated_game_code · method · L15-L28 — async def test_public_and_private_rooms_store_validated_game_code(self)
- test_invalid_game_is_rejected_before_room_creation · method · L30-L34 — async def test_invalid_game_is_rejected_before_room_creation(self)
- test_missing_or_different_game_cannot_ready · method · L36-L44 — async def test_missing_or_different_game_cannot_ready(self)
- test_three_matching_players_start_and_can_cancel · method · L46-L56 — async def test_three_matching_players_start_and_can_cancel(self)
- test_basic_room_still_accepts_ready_without_custom_code · method · L58-L67 — async def test_basic_room_still_accepts_ready_without_custom_code(self)
- test_migration_keeps_existing_rooms · method · L69-L81 — def test_migration_keeps_existing_rooms(self)
