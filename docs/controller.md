# CortexMesh Controller

The Controller is the central brain of a CortexMesh cluster. It provides the API, manages the database, runs the scheduler, and coordinates all nodes.

## Components

- **FastAPI Server** — REST API and WebSocket
- **Database** — SQLite (default) or PostgreSQL
- **Scheduler** — Capability-based task placement
- **Auth** — Enrollment tokens, role-based access
- **Audit Log** — All administrative actions recorded

## Starting the Controller

```bash
cortexctl controller --host 0.0.0.0 --port 8000
```

Or via Python:

```python
import uvicorn
uvicorn.run("cortexmesh.server.api:app", host="0.0.0.0", port=8000)
```

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8000` | Bind port |
| `--db` | `sqlite+aiosqlite:///./cortexmesh.db` | Database URL |

### Environment Variables

- `DATABASE_URL` — Database connection string
- `HERMESMESH_SECRET` — Secret key for signing

## API Endpoints

See [API Reference](api.md) for complete endpoint documentation.

## Database Schema

The controller uses SQLAlchemy with the following tables:

- `nodes` — Registered cluster nodes
- `tasks` — Task queue and history
- `providers` — Configured model providers
- `events` — Cluster events
- `audit_log` — Administrative actions
- `enrollment_tokens` — Node enrollment tokens
- `storage_locations` — Registered storage paths
- `resource_leases` — Active resource reservations
- `policies` — Resource policies

## Scheduler

The scheduler uses capability-based scoring to place tasks on the best available node. See [Scheduler](scheduler.md) for details.

## Security

- All API endpoints require authentication (except health and enrollment)
- Enrollment tokens are single-use and expire
- Audit log tracks all changes
- TLS recommended for production

## Production Deployment

```bash
# Using gunicorn with uvicorn workers
gunicorn cortexmesh.server.api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Behind nginx reverse proxy
# See docs/deployment.md for full guide
```

## Monitoring

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Cluster status
cortexctl status --controller http://localhost:8000

# Recent events
cortexctl event list --controller http://localhost:8000
```
