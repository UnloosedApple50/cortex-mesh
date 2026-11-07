# CortexMesh — Deployment Guide

## Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 10 GB | 50+ GB |
| OS | Linux (Ubuntu 20.04+) | Linux (Ubuntu 22.04+) |
| Python | 3.8+ | 3.11+ |
| Network | 1 node | 2+ nodes |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Controller Node                        │
│              FastAPI + Scheduler + Database                 │
│                      Port: 8000                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Worker 1 │  │ Worker 2 │  │ Worker N │
        │  Agent   │  │  Agent   │  │  Agent   │
        └──────────┘  └──────────┘  └──────────┘
```

---

## Quick Start

### 1. Install

```bash
pip install cortexmesh
```

### 2. Start Controller

```bash
cortexctl controller --host 0.0.0.0 --port 8000
```

### 3. Generate Enrollment Token

```bash
curl -X POST http://localhost:8000/api/v1/enrollment/create
```

### 4. Start Agent (on each node)

```bash
cortexctl agent --controller http://<controller-ip>:8000 --token <token>
```

---

## Node Roles

| Role | Description |
|------|-------------|
| **Controller** | Runs the API, scheduler, and database |
| **Worker** | Runs tasks assigned by the controller |
| **Client** | Connects to the API to submit tasks |

---

## Hardware Detection

The agent automatically detects and reports:

- CPU cores and frequency
- RAM (total and available)
- GPU (NVIDIA, AMD, Intel, Apple)
- Storage (total and available)
- Platform and architecture

---

## Scaling

Add more worker nodes to increase capacity:

```bash
# On each new node
cortexctl agent --controller http://<controller-ip>:8000 --token <token>
```

The scheduler automatically distributes tasks based on available resources.

---

## Troubleshooting

```bash
# Check controller health
curl http://localhost:8000/api/v1/health

# List nodes
cortexctl node list --controller http://localhost:8000

# Check node status
cortexctl status --controller http://localhost:8000
```

---

## Docker Deployment

```bash
docker build -t cortexmesh .
docker run -d -p 8000:8000 cortexmesh
```

Or use docker-compose:

```bash
docker compose up -d
```
