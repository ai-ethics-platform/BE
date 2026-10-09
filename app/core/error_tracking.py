"""Privacy-conscious exception reporting to PostHog Error Tracking."""

import logging
import os
from uuid import UUID
from typing import Optional

from posthog import Posthog

logger = logging.getLogger(__name__)

_token = os.getenv("POSTHOG_PROJECT_TOKEN")
posthog_client: Optional[Posthog] = (
    Posthog(
        project_api_key=_token,
        host=os.getenv("POSTHOG_HOST", "https://us.i.posthog.com"),
        enable_exception_autocapture=True,
        disable_geoip=True,
        privacy_mode=True,
    )
    if _token
    else None
)


def capture_exception(error: Exception, endpoint: str, session_id: Optional[str] = None) -> None:
    """Report an exception without request data, identifiers, or credentials."""
    if posthog_client is None:
        return

    try:
        properties = {"endpoint": endpoint, "$process_person_profile": False}
        if session_id:
            try:
                if UUID(session_id).version == 7:
                    properties["$session_id"] = session_id
            except ValueError:
                pass
        posthog_client.capture_exception(
            error,
            distinct_id="backend",
            properties=properties,
        )
    except Exception:
        # Telemetry outages must never affect API behavior.
        logger.exception("Failed to report exception to PostHog")


def shutdown_error_tracking() -> None:
    if posthog_client is not None:
        posthog_client.shutdown()
