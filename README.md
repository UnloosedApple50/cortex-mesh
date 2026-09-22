# CortexMesh

**Universal Platform for Multi-Machine Orchestration**

A platform that transforms multiple independent computers into a logical cluster of computational resources.

## Vision

Treat a cluster as **a set of independent machines with different capabilities, managed by a central scheduler.**

## Status

🚧 **Active Development** — Phase 1: Foundation

### What's Implemented

- ✅ **Controller** — FastAPI REST API with health, nodes, tasks, providers, storage, events
- ✅ **Agent** — Hardware detection, registration, heartbeat
- ✅ **Scheduler** — Capability-based scoring and task placement
- ✅ **Database** — SQLAlchemy async with SQLite/PostgreSQL support
- ✅ **CLI** — Complete `cortexctl` tool with 19+ commands
- ✅ **Tests** — Comprehensive test coverage (scheduler, API, agent, CLI)
- ✅ **CI/CD** — GitHub Actions workflow (lint, type check, tests)
- ✅ **Documentation** — Full docs covering installation, usage, security, troubleshooting

## Architecture

CortexMesh follows a **Capability-Driven Architecture**:

- **Controller** — Brain: API, scheduler, authentication, registry
- **Agent** — Runs on each node: detects capabilities, reports health
- **Scheduler** — Capability-based scoring and task placement
- **Adapters** — Abstract hardware/OS differences
- **CLI** — Administration tool (`cortexctl`)

## Principles

1. **No hardware assumptions** — Detect, don't assume
2. **Capability-driven** — Score based on actual capabilities
3. **Safe by default** — No destructive automation, no secrets in git
4. **Graceful degradation** — Features degrade when unavailable
5. **Observable** — Every decision is explainable

## Quick Start

```bash
# Install
pip install cortexmesh

# Start Controller
cortexctl controller --host 0.0.0.0 --port 8000

# Generate enrollment token
curl -X POST http://localhost:8000/api/v1/enrollment/create

# Start Agent (on each node)
cortexctl agent --controller http://localhost:8000 --token <token>

# Check status
cortexctl status --controller http://localhost:8000
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `cortexctl controller` | Start the controller |
| `cortexctl agent` | Start an agent |
| `cortexctl doctor` | Run diagnostics |
| `cortexctl status` | Show cluster status |
| `cortexctl version` | Show version |
| `cortexctl node list` | List all nodes |
| `cortexctl node info <id>` | Show node details |
| `cortexctl node enable <id>` | Enable a node |
| `cortexctl node disable <id>` | Disable a node |
| `cortexctl task list` | List tasks |
| `cortexctl task submit` | Submit a task |
| `cortexctl task cancel <id>` | Cancel a task |
| `cortexctl model list` | List available models |
| `cortexctl provider list` | List providers |
| `cortexctl provider test <id>` | Test provider |
| `cortexctl storage list` | List storage locations |
| `cortexctl profile list` | List profiles |
| `cortexctl profile apply <name>` | Apply a profile |
| `cortexctl event list` | List recent events |
| `cortexctl config show` | Show configuration |
| `cortexctl config set <key> <value>` | Set configuration |
| `cortexctl logs` | Show recent logs |

## Documentation

- [Installation](docs/installation.md)
- [Agent](docs/agent.md)
- [Controller](docs/controller.md)
- [Scheduler](docs/scheduler.md)
- [Security](docs/security.md)
- [API Reference](docs/api.md)
- [Development](docs/development.md)
- [Troubleshooting](docs/troubleshooting.md)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cortexmesh --cov-report=html

# Run specific tests
pytest tests/test_scheduler.py
pytest tests/test_api.py
pytest tests/test_agent.py
pytest tests/test_cli.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [SECURITY.md](SECURITY.md) for security policy.

## License

MIT License — see [LICENSE](LICENSE) for details.
