# HermesMesh Architecture

## Overview

HermesMesh transforms multiple independent computers into a logical cluster.

The system separates **Control Plane** from **Data Plane**:

- **Control Plane**: Controller, API, Scheduler, Database, Auth
- **Data Plane**: Agents, Model execution, File transfer, Remote access

## Core Concepts

### Node

A registered machine with:
- Persistent UUID identity
- Platform (Linux/Windows/macOS)
- Architecture (x86_64/arm64)
- Capabilities (CPU, RAM, GPU, Storage, Network)
- Roles (worker, storage, gpu_worker, client, monitor)

### Capability

A capability is a **fact** about a node:
- CPU: 16 threads, x86_64
- GPU: NVIDIA RTX 4060, 8GB VRAM
- Storage: 1TB NVMe
- Provider: Ollama installed

Capabilities are **discovered**, never assumed.

### Task

A unit of work with:
- Requirements (CPU, RAM, VRAM, provider, model)
- Priority (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND)
- State machine (QUEUED → SCHEDULED → RUNNING → COMPLETED)
- Resource lease

### Scheduler

Scoring-based selection:
1. Filter by capabilities (eliminate impossible nodes)
2. Score remaining nodes (configurable weights)
3. Reserve resources (lease)
4. Launch task

### Adapter Pattern

Hardware and OS abstraction:

```
adapters/
├── platform/
│   ├── linux/       # systemd, cgroups, procfs
│   ├── windows/     # WMI, PowerShell, Job Objects
│   └── macos/       # sysctl, launchd, ioreg
├── gpu/
│   ├── nvidia/      # NVML, nvidia-smi
│   ├── amd/         # ROCm
│   ├── intel/       # Level Zero
│   ├── apple/       # Metal, unified memory
│   └── generic/     # fallback
├── storage/
│   ├── local/       # filesystem
│   └── remote/      # network storage
└── model_providers/
    ├── ollama/      # Ollama API
    ├── openai/      # OpenAI-compatible
    ├── llamacpp/    # llama.cpp
    └── vllm/        # vLLM
```

## Control Plane vs Data Plane

```
┌─────────────────────────────────────────┐
│              CONTROLLER                 │
│  ┌──────────┐  ┌─────────────────────┐ │
│  │   API    │  │     Scheduler       │ │
│  │ REST     │  │  Score → Reserve →  │ │
│  │ WS       │  │  Launch             │ │
│  └──────────┘  └─────────────────────┘ │
│  ┌──────────┐  ┌─────────────────────┐ │
│  │ Database │  │   Auth / Audit      │ │
│  │ Nodes    │  │   Enrollment        │ │
│  │ Tasks    │  │   Permissions       │ │
│  └──────────┘  └─────────────────────┘ │
└─────────────────────────────────────────┘
           │ Secure Connection
     ┌─────┼─────┬─────────┐
     ▼     ▼     ▼         ▼
   ┌───┐ ┌───┐ ┌───┐   ┌───┐
   │ A │ │ B │ │ C │   │ D │  Agents
   └───┘ └───┘ └───┘   └───┘
```

## Security Model

- Enrollment tokens (single-use, expiring)
- TLS everywhere
- Node credentials (rotatable, signed requests)
- Role-based access (ADMIN, OPERATOR, VIEWER)
- Audit log for all administrative actions

## Data Flow

### Node Enrollment

```
User installs agent → Agent starts → User provides enrollment code
→ Agent authenticates → Controller registers node → Node appears in dashboard
```

### Task Execution

```
User submits task → API validates → Scheduler scores nodes
→ Resource lease → Stage model (if needed) → Launch → Monitor → Complete
```

## Database Schema (v1)

- **nodes** — Registry of all known machines
- **capabilities** — Per-node capability facts
- **tasks** — Task queue and history
- **resource_leases** — Active resource reservations
- **providers** — Configured model providers
- **models** — Discovered models
- **storage_locations** — Registered storage paths
- **events** — Cluster events
- **audit_log** — Administrative actions
- **policies** — Resource policies

## Platform Detection

The agent detects at startup:
- OS and architecture
- CPU cores, threads, frequency
- Memory total/available
- GPU vendor, model, VRAM
- Storage devices and free space
- Network interfaces
- Installed providers (Ollama, etc.)

## State Machine

### Node States
```
ONLINE → DEGRADED → UNREACHABLE → OFFLINE
                     ↓
                  MAINTENANCE
```

### Task States
```
QUEUED → RESERVED → SCHEDULED → STARTING → RUNNING → COMPLETED
                                                 → FAILED
                                                 → CANCELLING → CANCELLED
                                                 → TIMEOUT → RETRYING
```

## Resource Policies

Each resource has:
- **usage**: Current utilization
- **limit**: Configured threshold
- **enforceable**: Can hard-limit be applied?
- **monitoring_only**: Observation only, no enforcement

Policy types:
- **Hard limit**: Platform can enforce (e.g., cgroups)
- **Soft limit**: Scheduler uses for decisions
- **Monitoring only**: Report, don't intervene

## Model Staging

```
Central Storage → Model Staging → Worker Local Cache → Inference
```

The scheduler considers:
- Model already present on node
- Free space on destination
- Network bandwidth and bandwidth cost
- Current workload

## Scheduler Scoring

Configurable weights for:
- CPU availability
- RAM availability
- GPU availability (if required)
- Model already cached
- Network latency
- Task priority
- Node preference

Decision is stored with explanation for debugging.

## Phase Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Foundation: DB, API, config | 🚧 In Progress |
| 2 | Agent: enrollment, heartbeat | 🔲 Planned |
| 3 | GPU adapters: NVIDIA, AMD, Intel, Apple | 🔲 Planned |
| 4 | Scheduler: scoring, leases, policies | 🔲 Planned |
| 5 | Providers: Ollama, OpenAI-compatible | 🔲 Planned |
| 6 | Storage and model staging | 🔲 Planned |
| 7 | Profiles and policies | 🔲 Planned |
| 8 | Remote access abstraction | 🔲 Planned |
| 9 | Desktop client | 🔲 Planned |
| 10 | Hardening: security, tests, docs | 🔲 Planned |
