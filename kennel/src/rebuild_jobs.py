# kennel/src/rebuild_jobs.py
import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


class RebuildStatus(str, Enum):
    pending  = "pending"
    running  = "running"
    done     = "done"
    failed   = "failed"


@dataclass
class RebuildJob:
    job_id:     str
    flavour:    str
    status:     RebuildStatus        = RebuildStatus.pending
    started_at: float | None         = None
    ended_at:   float | None         = None
    error:      str | None           = None
    # Rolling log buffer — last 2000 lines
    # Subscribers read from this via asyncio.Queue
    _log_lines: deque                = field(default_factory=lambda: deque(maxlen=2000))
    _subscribers: list               = field(default_factory=list)

    def append_log(self, line: str):
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        self._log_lines.append(stamped)
        # Fan out to any live WebSocket subscribers
        dead = []
        for q in self._subscribers:
            try:
                q.put_nowait(stamped)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._subscribers.remove(q)

    def subscribe(self) -> asyncio.Queue:
        """Returns a queue that receives future log lines."""
        q: asyncio.Queue = asyncio.Queue(maxsize=500)
        # Replay existing lines first
        for line in self._log_lines:
            try:
                q.put_nowait(line)
            except asyncio.QueueFull:
                break
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass

    @property
    def log_lines(self) -> list[str]:
        return list(self._log_lines)


class RebuildJobStore:
    def __init__(self):
        self._jobs: dict[str, RebuildJob] = {}
        # Most recent job per flavour for quick lookup
        self._by_flavour: dict[str, str] = {}

    def create(self, job_id: str, flavour: str) -> RebuildJob:
        job = RebuildJob(job_id=job_id, flavour=flavour)
        self._jobs[job_id] = job
        self._by_flavour[flavour] = job_id
        return job

    def get(self, job_id: str) -> RebuildJob | None:
        return self._jobs.get(job_id)

    def latest_for(self, flavour: str) -> RebuildJob | None:
        job_id = self._by_flavour.get(flavour)
        return self._jobs.get(job_id) if job_id else None

    def all(self) -> list[RebuildJob]:
        return list(self._jobs.values())


rebuild_store = RebuildJobStore()