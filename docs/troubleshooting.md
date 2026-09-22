# HermesMesh Troubleshooting

## Common Issues

### Controller won't start

```bash
# Check if port is in use
lsof -i :8000

# Check database permissions
ls -la hermesmesh.db

# Run with debug logging
hermesctl controller --port 8001
```

### Agent can't connect to controller

```bash
# Test connectivity
curl http://localhost:8000/api/v1/health

# Check firewall
sudo ufw status
sudo ufw allow 8000/tcp

# Verify enrollment token
curl -X POST http://localhost:8000/api/v1/enrollment/create
```

### Node shows as OFFLINE

```bash
# Check agent logs
journalctl -u hermesmesh-agent -f

# Verify heartbeat interval
hermesctl agent --controller http://localhost:8000 --token <token>

# Check controller logs
hermesctl logs --lines 100
```

### Task stuck in QUEUED state

```bash
# Check if any nodes are online
hermesctl node list --controller http://localhost:8000

# Check node capabilities match task requirements
hermesctl node info <node_id> --controller http://localhost:8000

# Check scheduler explanation
hermesctl task info <task_id> --controller http://localhost:8000
```

### GPU not detected

```bash
# NVIDIA
nvidia-smi

# Check driver version
cat /proc/driver/nvidia/version

# AMD (Linux)
lspci | grep -i vga
rocm-smi

# Apple Silicon
system_profiler SPDisplaysDataType
```

### Database errors

```bash
# Reset database (WARNING: destroys all data)
rm hermesmesh.db
hermesctl controller

# Check database integrity
sqlite3 hermesmesh.db "PRAGMA integrity_check;"
```

## Debug Mode

Enable verbose logging:

```bash
# Set log level
export HERMESMESH_LOG_LEVEL=debug

# Start controller
hermesctl controller
```

## Getting Help

1. Check the [FAQ](faq.md)
2. Search [GitHub Issues](https://github.com/hermesmesh/hermesmesh/issues)
3. Join the community Discord
4. Open a new issue with:
   - HermesMesh version (`hermesctl version`)
   - Python version (`python --version`)
   - OS and architecture
   - Steps to reproduce
   - Error messages and logs
