import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from app.core.game_diagnostics import context_from_headers, record_request


class GameDiagnosticsTests(unittest.TestCase):
    def test_missing_metadata_is_not_reported_as_missing_game_code(self):
        self.assertEqual(context_from_headers({}), {'context_status': 'missing'})

    def test_malformed_and_oversized_metadata(self):
        for raw in ['[]', 'bad json', 'x' * 1501]:
            self.assertEqual(context_from_headers({'x-game-context': raw}), {'context_status': 'invalid'})

    def test_only_bounded_context_is_kept(self):
        values = dict(version=1, path='/gameintro', game_code='GAME_A', url_code=None,
                      password='never-record', access_token='never-record', page_id='page-1')
        actual = context_from_headers({'x-game-context': json.dumps(values)})
        self.assertEqual(actual['game_code'], 'GAME_A')
        self.assertIsNone(actual['url_code'])
        self.assertNotIn('password', actual)
        self.assertNotIn('access_token', actual)

    def test_server_account_is_correlated_without_identity_or_body(self):
        request = SimpleNamespace(method='POST', url=SimpleNamespace(path='/auth/login'),
            state=SimpleNamespace(diagnostic_user_id=123), headers={}, path_params={},
            scope={'route': SimpleNamespace(path='/auth/login')})
        with patch('app.core.game_diagnostics.capture_event') as capture, patch.dict('os.environ', {'GAME_DIAGNOSTIC_URL': ''}):
            record_request(request, 200)
        payload = capture.call_args.args[1]
        self.assertEqual(len(payload['account_ref']), 16)
        self.assertNotIn('user_id', payload)
        self.assertEqual(payload['context_status'], 'missing')
