# HermesMesh Scheduler

The scheduler is responsible for placing tasks on the best available node in the cluster.

## Algorithm

The scheduler uses a **capability-based scoring** algorithm:

1. **Filter** — Eliminate nodes that don't meet hard requirements
2. **Score** — Calculate a weighted score for each eligible node
3. **Select** — Choose the highest-scoring node
4. **Reserve** — Create a resource lease
5. **Explain** — Store human-readable decision explanation

## Scoring Weights

| Factor | Default Weight | Description |
|--------|---------------|-------------|
| CPU | 1.0 | Available CPU threads |
| Memory | 1.5 | Available RAM |
| GPU | 2.0 | Available VRAM |
| Model Cached | 3.0 | Model already on node |
| Load | 1.0 | Current node load |
| Preference | 0.5 | User-configured preference |

## Task Requirements

Each task specifies requirements:

```python
{
    "cpu_threads": 4,        # Minimum CPU threads
    "memory_gb": 8,          # Minimum RAM in GB
    "gpu_required": true,    # GPU needed
    "vram_gb": 6,            # Minimum VRAM in GB
    "provider": "ollama",    # Required provider
    "model_name": "llama3"   # Required model
}
```

## Node Eligibility

A node is eligible if:
- State is `ONLINE`
- Has `WORKER` role (not `CLIENT`-only)
- Meets all hard requirements (CPU, RAM, VRAM)

## Scoring Example

Given a task requiring 4 CPU threads, 8GB RAM, and 6GB VRAM:

```
Node A: 16 threads, 32GB RAM, RTX 4060 (8GB VRAM)
  CPU score: min(1.0, 16/8) * 1.0 = 1.0
  RAM score: min(1.0, 32/16) * 1.5 = 1.5
  VRAM score: min(1.0, 8/12) * 2.0 = 1.33
  Total: 3.83

Node B: 8 threads, 16GB RAM, no GPU
  REJECTED (GPU required)
```

## Resource Leases

When a task is scheduled, a resource lease is created to prevent overcommitment. Leases are released when tasks complete or fail.

## Configuration

```python
from hermesmesh.core.scheduler import CapabilityScorer

scorer = CapabilityScorer(
    weight_cpu=1.0,
    weight_memory=1.5,
    weight_gpu=2.0,
    weight_model_cached=3.0,
    weight_load=1.0,
    weight_preference=0.5,
)
scheduler = Scheduler(scorer=scorer)
```

## Decision Explanation

Every scheduling decision includes a human-readable explanation:

```
Selected Node: node-a
Score: 5.83
Reasons:
  - CPU: 16 threads available
  - RAM: 32.0GB available
  - GPU: RTX 4060 (8.0GB VRAM)
  - Model 'llama3' already cached
  - Load: 25%

Other nodes considered:
  - node-b: GPU required but not available
  - node-c: score=2.10
```

## Future Enhancements

- Network latency scoring
- Task affinity (prefer same node for related tasks)
- Preemption for high-priority tasks
- Multi-node task distribution
