"""
Unified outbox worker - processes multiple job types.

Polls multiple outbox tables and processes jobs in a single worker process.
This reduces container overhead while maintaining separation of concerns.

Configuration via env vars:
- OUTBOX_POLL_INTERVAL_SECONDS (default: 5)
- OUTBOX_WORKER_ID (default: outbox-worker-1)
- OUTBOX_LOG_LEVEL (default: INFO)

Run:
    python -m app.services.outbox_worker
"""

from __future__ import annotations

import logging
import os
import socket
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlmodel import Session

from app.core.db import engine

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = int(os.getenv("OUTBOX_POLL_INTERVAL_SECONDS", "5"))
WORKER_ID = os.getenv("OUTBOX_WORKER_ID") or f"outbox-{socket.gethostname()}:{os.getpid()}"


@dataclass
class JobProcessor:
    """A registered job type with its claim and process functions."""

    name: str
    claim_fn: Callable[[Session, str], list[Any]]  # Returns job IDs
    process_fn: Callable[[Any, str], None]  # Processes single job
    enabled: bool = True


# Registry of job processors
_processors: list[JobProcessor] = []


def register_processor(
    name: str,
    claim_fn: Callable[[Session, str], list[Any]],
    process_fn: Callable[[Any, str], None],
    enabled: bool = True,
) -> None:
    """Register a job processor."""
    _processors.append(
        JobProcessor(name=name, claim_fn=claim_fn, process_fn=process_fn, enabled=enabled)
    )


def run_worker() -> None:
    """Main unified worker loop."""
    logging.basicConfig(
        level=os.getenv("OUTBOX_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    enabled_processors = [p for p in _processors if p.enabled]
    logger.info(
        f"Unified outbox worker starting (id={WORKER_ID}, "
        f"poll={POLL_INTERVAL_SECONDS}s, "
        f"processors={[p.name for p in enabled_processors]})"
    )

    if not enabled_processors:
        logger.warning("No processors enabled - worker will idle")

    while True:
        jobs_processed = 0

        for processor in enabled_processors:
            try:
                with Session(engine) as session:
                    job_ids = processor.claim_fn(session, WORKER_ID)

                for job_id in job_ids:
                    try:
                        processor.process_fn(job_id, WORKER_ID)
                        jobs_processed += 1
                    except Exception as exc:
                        logger.exception(
                            f"Error processing {processor.name} job {job_id}: {exc}"
                        )

            except Exception as exc:
                logger.exception(f"Error in {processor.name} claim phase: {exc}")

        if jobs_processed == 0:
            time.sleep(POLL_INTERVAL_SECONDS)


def _init_processors() -> None:
    """Initialize and register all job processors."""
    # Shadow outbox processor
    shadow_enabled = os.getenv("OUTBOX_SHADOW_ENABLED", "true").lower() in ("true", "1", "yes")
    if shadow_enabled:
        from app.services.shadow_outbox_worker import (
            _claim_jobs as shadow_claim,
            _process_job as shadow_process,
        )
        register_processor("shadow", shadow_claim, shadow_process, enabled=True)
        logger.debug("Registered shadow outbox processor")

    # User repo outbox processor
    user_repo_enabled = os.getenv("OUTBOX_USER_REPO_ENABLED", "true").lower() in ("true", "1", "yes")
    if user_repo_enabled:
        from app.services.user_repo_outbox_worker import (
            _claim_jobs as user_repo_claim,
            _process_job as user_repo_process,
        )
        register_processor("user_repo", user_repo_claim, user_repo_process, enabled=True)
        logger.debug("Registered user_repo outbox processor")


# Initialize processors at module load
_init_processors()


if __name__ == "__main__":
    run_worker()
