from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RenderRequest:
    script_id: str
    params: dict[str, Any] = field(default_factory=dict)
    output_dir: str = "artifacts"
    formats: list[str] = field(default_factory=lambda: ["svg"])
    basename: str = "render"
    request_id: str | None = None
    runtime_profile: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RenderRequest":
        script_id = payload.get("script_id")
        if not isinstance(script_id, str) or not script_id.strip():
            raise ValueError("script_id is required and must be a non-empty string")

        params = payload.get("params", {})
        if not isinstance(params, dict):
            raise ValueError("params must be an object")

        output_dir = payload.get("output_dir", "artifacts")
        if not isinstance(output_dir, str) or not output_dir.strip():
            raise ValueError("output_dir must be a non-empty string")

        formats = payload.get("formats", ["svg"])
        if not isinstance(formats, list) or not all(
            isinstance(item, str) and item for item in formats
        ):
            raise ValueError("formats must be a list of non-empty strings")

        basename = payload.get("basename", "render")
        if not isinstance(basename, str) or not basename.strip():
            raise ValueError("basename must be a non-empty string")

        request_id = payload.get("request_id")
        if request_id is not None and not isinstance(request_id, str):
            raise ValueError("request_id must be a string when provided")

        runtime_profile = payload.get("runtime_profile")
        if runtime_profile is not None and not isinstance(runtime_profile, str):
            raise ValueError("runtime_profile must be a string when provided")

        return cls(
            script_id=script_id,
            params=params,
            output_dir=output_dir,
            formats=formats,
            basename=basename,
            request_id=request_id,
            runtime_profile=runtime_profile,
        )


@dataclass(slots=True)
class RenderArtifact:
    path: str
    media_type: str
    size_bytes: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "media_type": self.media_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(slots=True)
class RenderResult:
    script_id: str
    status: str
    artifacts: list[RenderArtifact]
    manifest_path: str
    request_id: str | None = None
    runtime_profile: str | None = None
    resolved_capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "script_id": self.script_id,
            "status": self.status,
            "request_id": self.request_id,
            "runtime_profile": self.runtime_profile,
            "resolved_capabilities": self.resolved_capabilities,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "manifest_path": self.manifest_path,
        }
