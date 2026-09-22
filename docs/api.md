# HermesMesh API Reference

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints (except health and enrollment) require authentication:

```
Authorization: Bearer <api_key>
```

## Endpoints

### Health

#### GET /api/v1/health

Returns controller health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600.0
}
```

#### GET /api/v1/version

Returns version information.

**Response:**
```json
{
  "version": "0.1.0",
  "api_version": "v1",
  "agent_protocol_version": "1"
}
```

### Nodes

#### GET /api/v1/nodes

List all registered nodes.

**Response:** Array of `NodeResponse`

```json
[
  {
    "node_id": "uuid",
    "hostname": "node1",
    "display_name": "Node 1",
    "platform": "linux",
    "architecture": "x86_64",
    "agent_version": "0.1.0",
    "roles": ["worker"],
    "state": "online",
    "capabilities": { ... },
    "last_seen": "2024-01-01T00:00:00Z",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /api/v1/nodes/{node_id}

Get a specific node by ID.

**Response:** `NodeResponse`

#### POST /api/v1/nodes/register

Register a new node.

**Request:**
```json
{
  "enrollment_token": "abc123",
  "hostname": "node1",
  "display_name": "Node 1",
  "platform": "linux",
  "architecture": "x86_64",
  "agent_version": "0.1.0",
  "capabilities": {
    "cpu": {"threads": 8, "architecture": "x86_64"},
    "memory": {"total_bytes": 17179869184, "available_bytes": 8589934592},
    "gpus": [],
    "storage": [],
    "network": {"interfaces": []}
  },
  "roles": ["worker"]
}
```

**Response:** `NodeResponse`

#### POST /api/v1/nodes/{node_id}/heartbeat

Send a node heartbeat.

**Response:**
```json
{"status": "ok"}
```

#### PATCH /api/v1/nodes/{node_id}

Update node properties.

**Request:**
```json
{"compute_enabled": false}
```

**Response:**
```json
{"status": "ok", "node_id": "uuid"}
```

#### DELETE /api/v1/nodes/{node_id}

Delete a node.

**Response:**
```json
{"success": true, "message": "Node deleted"}
```

### Tasks

#### GET /api/v1/tasks

List all tasks.

**Query Parameters:**
- `state` — Filter by state (queued, running, completed, etc.)

**Response:** Array of `TaskResponse`

#### POST /api/v1/tasks

Submit a new task.

**Request:**
```json
{
  "task_type": "chat",
  "title": "My Task",
  "description": "Optional description",
  "requirements": {
    "cpu_threads": 2,
    "memory_gb": 4,
    "gpu_required": false,
    "vram_gb": null,
    "provider": "ollama",
    "model_name": "llama3"
  },
  "priority": "normal",
  "timeout_seconds": 3600,
  "max_retries": 0,
  "payload": {},
  "idempotency_key": null
}
```

**Response:** `TaskResponse`

#### GET /api/v1/tasks/{task_id}

Get a specific task.

**Response:** `TaskResponse`

#### POST /api/v1/tasks/{task_id}/cancel

Cancel a task.

**Response:**
```json
{"success": true, "message": "Cancellation requested"}
```

### Providers

#### GET /api/v1/providers

List configured model providers.

**Response:** Array of `ProviderResponse`

#### POST /api/v1/providers

Create a new provider.

**Request:**
```json
{
  "provider_type": "ollama",
  "endpoint": "http://localhost:11434",
  "name": "Local Ollama",
  "api_key": null,
  "extra_config": {}
}
```

**Response:** `ProviderResponse`

### Storage

#### GET /api/v1/storage

List storage locations.

**Response:** Array of `StorageLocation`

### Events

#### GET /api/v1/events

List recent events.

**Query Parameters:**
- `limit` — Number of events to return (default: 100)

**Response:** Array of `Event`

### Enrollment

#### POST /api/v1/enrollment/create

Create a new enrollment token.

**Query Parameters:**
- `expires_hours` — Token expiry in hours (default: 24)

**Response:**
```json
{
  "token_id": "uuid",
  "token": "abc123def456",
  "expires_at": "2024-01-02T00:00:00Z",
  "is_used": false,
  "used_by_node_id": null,
  "used_at": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### WebSocket

#### /ws

Real-time event stream.

**Messages:**
```json
{
  "echo": "hello",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": "Error type",
  "detail": "Human-readable description",
  "code": "ERROR_CODE"
}
```

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Conflict |
| 500 | Internal server error |
