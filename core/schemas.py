from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "2.0.0"
    services: Dict[str, str] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    persona: Optional[str] = None
    model: Optional[str] = None
    tools: Optional[List[str]] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    intent: str = "qa"
    tool_used: Optional[str] = None
    model_used: Optional[str] = None
    sources: Optional[List[Dict[str, str]]] = None
    thinking: Optional[str] = None


class HistoryEntry(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    timestamp: str
    intent: Optional[str] = None


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    message_count: int
    title: Optional[str] = None


class ContainerInfo(BaseModel):
    name: str
    status: str
    image: str
    ports: str = ""
    created: str = ""


class HomelabStatus(BaseModel):
    host_reachable: bool
    containers: List[ContainerInfo] = Field(default_factory=list)
    ssh_user: str = ""
    ssh_host: str = ""


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str
    due_date: Optional[str]
    created_at: str
    updated_at: str


class UploadResponse(BaseModel):
    filename: str
    path: str
    size: int


class ExportRequest(BaseModel):
    session_id: Optional[str] = None
    format: str = "json"


class SettingsUpdate(BaseModel):
    key: str
    value: str


class AgentCreate(BaseModel):
    name: str
    description: str = ""
    system_prompt: str = ""
    model: Optional[str] = None
    tools: List[str] = Field(default_factory=list)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    tools: Optional[List[str]] = None


class AgentOut(BaseModel):
    id: int
    name: str
    description: str
    system_prompt: str
    model: Optional[str]
    tools: List[str]
    created_at: str
    updated_at: str



class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str = "zen"
    context_window: int = 4096
    is_default: bool = False


class ModelsResponse(BaseModel):
    models: List[ModelInfo] = Field(default_factory=list)
    default: str = ""
