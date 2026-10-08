"""Privacy-conscious exception reporting to PostHog Error Tracking."""

import logging
import os
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


def capture_exception(error: Exception, endpoint: str) -> None:
    """Report an exception without request data, identifiers, or credentials."""
    if posthog_client is None:
        return

    try:
        posthog_client.capture_exception(
            error,
            "backend",
            {"endpoint": endpoint, "$process_person_profile": False},
        )
    except Exception:
        # Telemetry outages must never affect API behavior.
        logger.exception("Failed to report exception to PostHog")


def shutdown_error_tracking() -> None:
    if posthog_client is not None:
        posthog_client.shutdown()
