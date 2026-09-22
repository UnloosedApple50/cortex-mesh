# HermesMesh

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
- ✅ **CLI** — Complete `hermesctl` tool with 19+ commands
- ✅ **Tests** — Comprehensive test coverage (scheduler, API, agent, CLI)
- ✅ **CI/CD** — GitHub Actions workflow (lint, type check, tests)
- ✅ **Documentation** — Full docs covering installation, usage, security, troubleshooting

## Architecture

HermesMesh follows a **Capability-Driven Architecture**:

- **Controller** — Brain: API, scheduler, authentication, registry
- **Agent** — Runs on each node: detects capabilities, reports health
- **Scheduler** — Capability-based scoring and task placement
- **Adapters** — Abstract hardware/OS differences
- **CLI** — Administration tool (`hermesctl`)

## Principles

1. **No hardware assumptions** — Detect, don't assume
2. **Capability-driven** — Score based on actual capabilities
3. **Safe by default** — No destructive automation, no secrets in git
4. **Graceful degradation** — Features degrade when unavailable
5. **Observable** — Every decision is explainable

## Quick Start

```bash
# Install
pip install hermesmesh

# Start Controller
hermesctl controller --host 0.0.0.0 --port 8000

# Generate enrollment token
curl -X POST http://localhost:8000/api/v1/enrollment/create

# Start Agent (on each node)
hermesctl agent --controller http://localhost:8000 --token <token>

# Check status
hermesctl status --controller http://localhost:8000
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `hermesctl controller` | Start the controller |
| `hermesctl agent` | Start an agent |
| `hermesctl doctor` | Run diagnostics |
| `hermesctl status` | Show cluster status |
| `hermesctl version` | Show version |
| `hermesctl node list` | List all nodes |
| `hermesctl node info <id>` | Show node details |
| `hermesctl node enable <id>` | Enable a node |
| `hermesctl node disable <id>` | Disable a node |
| `hermesctl task list` | List tasks |
| `hermesctl task submit` | Submit a task |
| `hermesctl task cancel <id>` | Cancel a task |
| `hermesctl model list` | List available models |
| `hermesctl provider list` | List providers |
| `hermesctl provider test <id>` | Test provider |
| `hermesctl storage list` | List storage locations |
| `hermesctl profile list` | List profiles |
| `hermesctl profile apply <name>` | Apply a profile |
| `hermesctl event list` | List recent events |
| `hermesctl config show` | Show configuration |
| `hermesctl config set <key> <value>` | Set configuration |
| `hermesctl logs` | Show recent logs |

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
pytest --cov=hermesmesh --cov-report=html

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
