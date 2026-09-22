# HermesMesh Agent

The HermesMesh Agent runs on each node in the cluster. It detects hardware capabilities, registers with the controller, and maintains a heartbeat connection.

## Responsibilities

1. **Hardware Detection** — CPU, memory, GPU, storage, network
2. **Registration** — Authenticates with controller using enrollment token
3. **Heartbeat** — Periodic health updates
4. **Task Execution** — Runs assigned tasks (future)

## Starting the Agent

```bash
hermesctl agent --controller http://localhost:8000 --token <token> --name my-node
```

## Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `--controller` | Required | Controller URL |
| `--token` | Required | Enrollment token |
| `--name` | Hostname | Display name for this node |

## Enrollment Flow

```
1. User generates enrollment token via API
2. User starts agent with token
3. Agent detects hardware capabilities
4. Agent registers with controller
5. Controller creates node record
6. Agent begins heartbeat loop
```

## Heartbeat

The agent sends heartbeats every 5 seconds (configurable). If the controller doesn't receive a heartbeat within a timeout period, the node is marked as `UNREACHABLE`.

## Capability Detection

The agent detects:

- **CPU**: Architecture, cores, threads, model name
- **Memory**: Total, available, swap
- **GPU**: Vendor (NVIDIA/AMD/Intel/Apple), model, VRAM, driver version
- **Storage**: Devices, mount points, filesystems, free space
- **Network**: Interfaces, IP addresses
- **Providers**: Installed model providers (Ollama, etc.)

## Security

- Enrollment tokens are single-use and expire after 24 hours
- All communication uses HTTPS in production
- Node credentials are stored locally

## Troubleshooting

### Agent can't connect to controller

```bash
# Test connectivity
curl http://localhost:8000/api/v1/health

# Check firewall rules
sudo ufw allow 8000/tcp
```

### GPU not detected

```bash
# NVIDIA
nvidia-smi

# AMD (Linux)
lspci | grep VGA

# Apple Silicon
system_profiler SPDisplaysDataType
```
