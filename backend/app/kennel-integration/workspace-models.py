# backend/app/models/workspace.py
import uuid
from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from typing import Any


class WorkspaceStatus(str, Enum):
    provisioning = "provisioning"   # kennel job in flight
    ready        = "ready"          # lxc running, ws available
    stopping     = "stopping"       # stop requested
    stopped      = "stopped"        # lxc stopped, data retained
    destroyed    = "destroyed"      # lxc destroyed, terminal


class WorkspaceFlavour(str, Enum):
    base    = "base"
    dev     = "dev"
    python  = "python"
    node    = "node"
    jupyter = "jupyter"


class WorkspaceBase(SQLModel):
    name:        str                   = Field(index=True)
    flavour:     WorkspaceFlavour      = Field(default=WorkspaceFlavour.dev)
    kind:        str                   = Field(default="ephemeral")  # ephemeral | persistent
    status:      WorkspaceStatus       = Field(default=WorkspaceStatus.provisioning)
    kennel_name: str | None            = Field(default=None)   # lxc container name
    kennel_job:  str | None            = Field(default=None)   # async job id
    ws_token:    str | None            = Field(default=None)   # terminal auth token
    meta:        dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))


class Workspace(WorkspaceBase, table=True):
    id:         uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id:   uuid.UUID = Field(foreign_key="user.id", index=True)
    created_at: datetime  = Field(default_factory=datetime.utcnow)
    updated_at: datetime  = Field(default_factory=datetime.utcnow)


class WorkspaceCreate(SQLModel):
    name:    str
    flavour: WorkspaceFlavour = WorkspaceFlavour.dev
    kind:    str              = "ephemeral"
    # optional workspace config — injected after spawn
    repo_url:    str | None = None
    ssh_pubkey:  str | None = None
    env_vars:    dict[str, str] = {}


class WorkspacePublic(WorkspaceBase):
    id:           uuid.UUID
    owner_id:     uuid.UUID
    created_at:   datetime
    terminal_url: str | None = None   # populated when status=ready