"""Bounded metadata shared by browser reports and the private admin receiver."""
import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

EVENTS = ('game_state_changed', 'custom_link_opened', 'custom_login_redirect', 'custom_game_load',
          'room_game_verified', 'waiting_room_game_context', 'game_start_transition',
          'game_intro_rendered', 'game_story_rendered', 'game_role_description_rendered',
          'navigation_received', 'navigation_selected', 'navigation_broadcast')
STRING_FIELDS = set(('source phase before_code before_loaded_code after_code after_loaded_code requested_code '
    'load_attempt_id message_id message_type destination story_source next_page_path error_code code_source diagnostic_version '
    'opening_fingerprint story_fingerprint role_descriptions_fingerprint').split())
NUMBER_FIELDS = set(('duration_ms status_code opening_count roles_count participant_count ready_count '
    'assigned_role_count slide_index paragraph_index description_role_id role_id connection_count sent_count').split())
BOOL_FIELDS = set(('custom_mode custom_game_ready code_present loaded_code_matches room_game_bound '
    'custom_game_code_present opening_parse_failed room_topic_matches_game_title').split())


def validate_details(values):
    if not isinstance(values, dict) or len(values) > 40:
        raise ValueError('Invalid diagnostic details')
    for key, value in values.items():
        if key in STRING_FIELDS and isinstance(value, str) and re.fullmatch(r'[\w./:-]{0,120}', value, re.ASCII):
            continue
        if key in NUMBER_FIELDS and type(value) is int and 0 <= value <= 100000000:
            continue
        if key in BOOL_FIELDS and type(value) is bool:
            continue
        raise ValueError('Invalid diagnostic detail')
    return values


class BrowserGameEvent(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: UUID
    at: datetime
    sequence: int = Field(ge=1, le=100000000)
    event: str = Field(max_length=60)
    context: dict
    details: dict = Field(default_factory=dict)

    @field_validator('event')
    @classmethod
    def known_event(cls, value):
        if value not in EVENTS or value == 'navigation_broadcast':
            raise ValueError('Unknown browser event')
        return value

    @field_validator('at')
    @classmethod
    def aware_time(cls, value):
        if value.tzinfo is None:
            raise ValueError('Timezone required')
        return value

    @field_validator('details')
    @classmethod
    def bounded_details(cls, value):
        return validate_details(value)


class BrowserGameBatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    events: list[BrowserGameEvent] = Field(min_length=1, max_length=5)
