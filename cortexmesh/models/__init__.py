"""
CortexMesh — Shared type contracts and Pydantic models.

All components (controller, agent, web, desktop) import from here
to ensure consistent data structures.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, validator


# ── Enums ────────────────────────────────────────────────────────

class Platform(str, Enum):
    LINUX = "linux"
    WINDOWS = "windows"
    MACOS = "macos"


class Architecture(str, Enum):
    X86_64 = "x86_64"
    ARM64 = "arm64"
    ARM = "arm"
    UNKNOWN = "unknown"


class NodeRole(str, Enum):
    CONTROLLER = "controller"
    WORKER = "worker"
    AI_WORKER = "ai_worker"
    GPU_WORKER = "gpu_worker"
    STORAGE = "storage"
    MONITOR = "monitor"
    REMOTE = "remote"
    CLIENT = "client"


class NodeState(str, Enum):
    ONLINE = "online"
    DEGRADED = "degraded"
    UNREACHABLE = "unreachable"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class GPUVendor(str, Enum):
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE = "apple"
    UNKNOWN = "unknown"


class ResourceType(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    VRAM = "vram"
    STORAGE = "storage"
    NETWORK = "network"


class TaskType(str, Enum):
    CHAT = "chat"
    INFERENCE = "inference"
    EMBEDDING = "embedding"
    BATCH = "batch"
    MODEL_OPERATION = "model_operation"
    FILE_OPERATION = "file_operation"
    MONITORING = "monitoring"
    CUSTOM = "custom"


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class TaskState(str, Enum):
    QUEUED = "queued"
    RESERVED = "reserved"
    SCHEDULED = "scheduled"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class Permission(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class PolicyType(str, Enum):
    HARD = "hard"
    SOFT = "soft"
    MONITORING_ONLY = "monitoring_only"


class ModelProviderType(str, Enum):
    OLLAMA = "ollama"
    OPENAI_COMPATIBLE = "openai_compatible"
    LLAMACPP = "llamacpp"
    VLLM = "vllm"
    CUSTOM = "custom"


# ── Base Models ──────────────────────────────────────────────────

class HermesBase(BaseModel):
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        },
    )


# ── Capabilities ────────────────────────────────────────────────

class CPUCapability(HermesBase):
    sockets: Optional[int] = None
    cores_physical: Optional[int] = None
    threads: Optional[int] = None
    frequency_mhz: Optional[float] = None
    architecture: Architecture = Architecture.UNKNOWN
    vendor: Optional[str] = None
    model: Optional[str] = None


class MemoryCapability(HermesBase):
    total_bytes: int = 0
    available_bytes: int = 0
    swap_total_bytes: int = 0
    swap_used_bytes: int = 0


class GPUCapability(HermesBase):
    vendor: GPUVendor = GPUVendor.UNKNOWN
    model: Optional[str] = None
    vram_bytes: Optional[int] = None
    driver_version: Optional[str] = None
    compute_capability: Optional[str] = None
    monitoring_supported: bool = False
    enforcement_supported: bool = False


class StorageCapability(HermesBase):
    device: str
    mount_point: str
    filesystem: Optional[str] = None
    total_bytes: int = 0
    used_bytes: int = 0
    free_bytes: int = 0
    is_removable: bool = False
    is_network: bool = False


class NetworkCapability(HermesBase):
    interfaces: List[Dict[str, Any]] = Field(default_factory=list)
    bandwidth_mbps: Optional[float] = None


class ProviderCapability(HermesBase):
    provider_type: ModelProviderType
    endpoint: Optional[str] = None
    is_available: bool = False
    models: List[str] = Field(default_factory=list)


class NodeCapabilities(HermesBase):
    cpu: CPUCapability = Field(default_factory=CPUCapability)
    memory: MemoryCapability = Field(default_factory=MemoryCapability)
    gpus: List[GPUCapability] = Field(default_factory=list)
    storage: List[StorageCapability] = Field(default_factory=list)
    network: NetworkCapability = Field(default_factory=NetworkCapability)
    providers: List[ProviderCapability] = Field(default_factory=list)


# ── Node ─────────────────────────────────────────────────────────

class NodeRegisterRequest(HermesBase):
    enrollment_token: str = Field(..., min_length=1)
    hostname: str
    display_name: Optional[str] = None
    platform: Platform
    architecture: Architecture
    agent_version: str
    capabilities: NodeCapabilities
    roles: List[NodeRole] = Field(default_factory=lambda: [NodeRole.WORKER])


class NodeHeartbeat(HermesBase):
    node_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    state: NodeState = NodeState.ONLINE
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    gpu_usage_percent: Optional[float] = None
    storage_usage_percent: Optional[float] = None
    tasks_running: int = 0
    capabilities_changed: bool = False


class NodeResponse(HermesBase):
    node_id: str
    hostname: str
    display_name: Optional[str] = None
    platform: Platform
    architecture: Architecture
    agent_version: str
    roles: List[NodeRole]
    state: NodeState
    capabilities: NodeCapabilities
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── Resources ────────────────────────────────────────────────────

class ResourceStatus(HermesBase):
    resource_type: ResourceType
    total: float
    used: float
    available: float
    unit: str = ""
    usage_percent: float = 0.0


class ResourceLimit(HermesBase):
    resource_type: ResourceType
    limit_value: float
    policy_type: PolicyType = PolicyType.SOFT
    unit: str = ""


# ── Task ─────────────────────────────────────────────────────────

class TaskRequirements(HermesBase):
    cpu_threads: Optional[int] = None
    memory_gb: Optional[float] = None
    gpu_required: bool = False
    vram_gb: Optional[float] = None
    provider: Optional[ModelProviderType] = None
    model_name: Optional[str] = None


class TaskSubmit(HermesBase):
    task_type: TaskType
    title: str
    description: Optional[str] = None
    requirements: TaskRequirements = Field(default_factory=TaskRequirements)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_seconds: int = 3600
    max_retries: int = 0
    payload: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None


class TaskResponse(HermesBase):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType
    title: str
    description: Optional[str] = None
    state: TaskState = TaskState.QUEUED
    priority: TaskPriority = TaskPriority.NORMAL
    node_id: Optional[str] = None
    node_hostname: Optional[str] = None
    requirements: TaskRequirements
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scheduler_explanation: Optional[str] = None


# ── Model Provider ───────────────────────────────────────────────

class ProviderCreate(HermesBase):
    provider_type: ModelProviderType
    endpoint: str
    name: Optional[str] = None
    api_key: Optional[str] = None
    extra_config: Dict[str, Any] = Field(default_factory=dict)


class ProviderResponse(HermesBase):
    provider_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_type: ModelProviderType
    endpoint: str
    name: Optional[str] = None
    is_available: bool = False
    models: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Model ────────────────────────────────────────────────────────

class ModelInfo(HermesBase):
    model_name: str
    provider_type: ModelProviderType
    provider_endpoint: Optional[str] = None
    size_bytes: Optional[int] = None
    context_length: Optional[int] = None
    requires_gpu: bool = False
    vram_gb: Optional[float] = None
    is_cached: bool = False
    node_ids: List[str] = Field(default_factory=list)


# ── Events ───────────────────────────────────────────────────────

class EventType(str, Enum):
    NODE_REGISTERED = "node_registered"
    NODE_OFFLINE = "node_offline"
    NODE_RECOVERED = "node_recovered"
    TASK_QUEUED = "task_queued"
    TASK_SCHEDULED = "task_scheduled"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    MODEL_DETECTED = "model_detected"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    POLICY_CHANGED = "policy_changed"
    ALERT = "alert"


class Event(HermesBase):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    source_node_id: Optional[str] = None
    source_task_id: Optional[str] = None
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Storage ──────────────────────────────────────────────────────

class StorageCategory(str, Enum):
    MODELS = "models"
    DATASETS = "datasets"
    BACKUPS = "backups"
    HERMES = "hermes"
    DOCKER = "docker"
    CACHE = "cache"
    FILES = "files"


class StorageLocation(HermesBase):
    location_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str
    path: str
    category: StorageCategory = StorageCategory.FILES
    total_bytes: int = 0
    used_bytes: int = 0
    free_bytes: int = 0
    is_available: bool = True


# ── Audit Log ────────────────────────────────────────────────────

class AuditEntry(HermesBase):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actor: str  # user or system
    action: str
    target: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Profile ──────────────────────────────────────────────────────

class Profile(HermesBase):
    profile_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    cpu_limit_percent: Optional[float] = Field(None, ge=0, le=100)
    memory_limit_percent: Optional[float] = Field(None, ge=0, le=100)
    gpu_scheduling_limit_percent: Optional[float] = Field(None, ge=0, le=100)
    priority: TaskPriority = TaskPriority.NORMAL
    allowed_hours_start: Optional[int] = Field(None, ge=0, le=23)
    allowed_hours_end: Optional[int] = Field(None, ge=0, le=23)
    allowed_node_roles: List[NodeRole] = Field(default_factory=list)


# ── Enrollment ───────────────────────────────────────────────────

class EnrollmentToken(HermesBase):
    token_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    expires_at: datetime
    is_used: bool = False
    used_by_node_id: Optional[str] = None
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Response Wrappers ────────────────────────────────────────────

class HealthResponse(HermesBase):
    status: str = "healthy"
    version: str = "0.1.0"
    uptime_seconds: float = 0.0


class VersionResponse(HermesBase):
    version: str = "0.1.0"
    api_version: str = "v1"
    agent_protocol_version: str = "1"


class SuccessResponse(HermesBase):
    success: bool = True
    message: str = "OK"


class ErrorResponse(HermesBase):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
