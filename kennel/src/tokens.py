# kennel/src/tokens.py
import asyncio
import secrets
import time
from dataclasses import dataclass, field


@dataclass
class WorkspaceToken:
    token:       str
    env_name:    str
    issued_at:   float = field(default_factory=time.monotonic)
    ttl_seconds: int   = 3600    # 1 hour — rotate on reconnect
    used:        bool  = False   # consumed on first WS connect


class TokenStore:
    """
    In-memory token store for prototype.
    Replace with Redis for multi-process / multi-node kennel.
    """
    def __init__(self):
        self._tokens: dict[str, WorkspaceToken] = {}
        self._by_env: dict[str, str] = {}          # env_name → token

    def issue(self, env_name: str, ttl: int = 3600) -> str:
        # Revoke any existing token for this env
        self.revoke_for_env(env_name)

        token = secrets.token_urlsafe(32)
        self._tokens[token] = WorkspaceToken(
            token=token, env_name=env_name, ttl_seconds=ttl
        )
        self._by_env[env_name] = token
        return token

    def validate(self, token: str, env_name: str) -> tuple[bool, str]:
        """
        Returns (valid, reason).
        Does NOT consume the token — WebSocket sessions can reconnect.
        Use revoke() explicitly on disconnect if you want single-use.
        """
        entry = self._tokens.get(token)

        if not entry:
            return False, "unknown token"
        if entry.env_name != env_name:
            return False, "token/env mismatch"
        if time.monotonic() - entry.issued_at > entry.ttl_seconds:
            self._expire(token)
            return False, "token expired"

        return True, "ok"

    def revoke(self, token: str) -> None:
        entry = self._tokens.pop(token, None)
        if entry:
            self._by_env.pop(entry.env_name, None)

    def revoke_for_env(self, env_name: str) -> None:
        token = self._by_env.get(env_name)
        if token:
            self.revoke(token)

    def _expire(self, token: str) -> None:
        self.revoke(token)

    async def reap_expired(self) -> None:
        """Background task — runs every 5 min to clean up expired tokens."""
        while True:
            await asyncio.sleep(300)
            now = time.monotonic()
            expired = [
                t for t, entry in self._tokens.items()
                if now - entry.issued_at > entry.ttl_seconds
            ]
            for t in expired:
                self._expire(t)


# Singleton — imported by server.py
token_store = TokenStore()