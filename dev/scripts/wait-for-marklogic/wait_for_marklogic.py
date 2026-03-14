"""Wait until MarkLogic is stable after startup or restart.

This probe intentionally uses only MarkLogic's ``/admin/v1/timestamp`` endpoint.
The MarkLogic REST API documentation describes this endpoint as the supported way
to verify that the server is up, accepting requests, and has completed a
restart. To avoid false positives during bootstrap, the script requires several
consecutive successful reads with the same timestamp value.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

import httpx

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 240
DEFAULT_POLL_INTERVAL = 5.0
DEFAULT_STABLE_ROUNDS = 3
DEFAULT_REQUEST_TIMEOUT = 5.0


def parse_args() -> argparse.Namespace:
    """Parse script arguments."""
    parser = argparse.ArgumentParser(
        description="Wait until MarkLogic completes restart and becomes stable.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--admin-port", type=int, default=8001)
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
    )
    parser.add_argument("--stable-rounds", type=int, default=DEFAULT_STABLE_ROUNDS)
    return parser.parse_args()


def fetch_timestamp(
    client: httpx.Client,
    host: str,
    admin_port: int,
    auth: httpx.DigestAuth,
) -> str:
    """Fetch the current MarkLogic restart timestamp from the admin endpoint."""
    timestamp_response = client.get(
        f"http://{host}:{admin_port}/admin/v1/timestamp",
        auth=auth,
    )
    timestamp_response.raise_for_status()
    return timestamp_response.text.strip()


def update_stability_counter(
    timestamp: str,
    previous_timestamp: str | None,
    stable_rounds: int,
) -> int:
    """Count consecutive successful reads of the same restart timestamp."""
    return stable_rounds + 1 if timestamp == previous_timestamp else 1


def main() -> int:
    """Wait for a stable MarkLogic bootstrap sequence to complete."""
    args = parse_args()
    deadline = time.monotonic() + args.timeout
    auth = httpx.DigestAuth(args.username, args.password)
    last_timestamp: str | None = None
    stable_rounds = 0

    while time.monotonic() < deadline:
        try:
            with httpx.Client(
                timeout=DEFAULT_REQUEST_TIMEOUT,
                headers={"Connection": "close"},
            ) as client:
                timestamp = fetch_timestamp(
                    client=client,
                    host=args.host,
                    admin_port=args.admin_port,
                    auth=auth,
                )

            stable_rounds = update_stability_counter(
                timestamp=timestamp,
                previous_timestamp=last_timestamp,
                stable_rounds=stable_rounds,
            )
            last_timestamp = timestamp
            logger.info(
                "Timestamp ready check passed (%s/%s) timestamp=%s",
                stable_rounds,
                args.stable_rounds,
                timestamp,
            )
            if stable_rounds >= args.stable_rounds:
                logger.info("MarkLogic is ready for integration tests.")
                return 0
        except Exception as exc:
            stable_rounds = 0
            logger.info("Waiting for MarkLogic: %s", exc)

        time.sleep(args.poll_interval)

    logger.error("Timed out waiting for MarkLogic readiness.")
    return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    raise SystemExit(main())
