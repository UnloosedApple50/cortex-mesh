# HermesMesh Installation

## Requirements

- Python 3.8 or higher
- pip or uv package manager
- (Optional) NVIDIA drivers for GPU support
- (Optional) Ollama for local model serving

## Install from PyPI

```bash
pip install hermesmesh
```

## Install from Source

```bash
git clone https://github.com/hermesmesh/hermesmesh.git
cd hermesmesh
pip install -e ".[dev]"
```

## Verify Installation

```bash
hermesctl version
hermesctl doctor
```

## Start the Controller

```bash
hermesctl controller --host 0.0.0.0 --port 8000
```

## Start an Agent

On each node you want to add to the cluster:

```bash
hermesctl agent --controller http://localhost:8000 --token <enrollment_token>
```

## Generate Enrollment Token

```bash
curl -X POST http://localhost:8000/api/v1/enrollment/create
```

## Docker (Optional)

```bash
docker build -t hermesmesh .
docker run -p 8000:8000 hermesmesh controller
```

## Platform-Specific Notes

### Linux

- Requires `nvidia-smi` for NVIDIA GPU detection
- Requires `lspci` for AMD GPU detection
- Requires `lsblk` for storage detection

### macOS

- Uses `sysctl` for CPU/memory detection
- Apple Silicon GPU detection built-in

### Windows

- Uses `wmic` for hardware detection
- NVIDIA GPU detection via `nvidia-smi`
