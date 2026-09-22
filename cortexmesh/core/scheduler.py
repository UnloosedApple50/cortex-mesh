"""
CortexMesh — Core scheduler with capability-based scoring.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from cortexmesh.models import (
    NodeCapabilities, NodeResponse, NodeRole, NodeState,
    TaskPriority, TaskRequirements, TaskState, TaskSubmit,
)


@dataclass
class ScoreResult:
    node_id: str
    hostname: str
    score: float
    explanation: List[str] = field(default_factory=list)


class CapabilityScorer:
    """
    Scores nodes based on task requirements and current state.
    
    Weights are configurable. Default weights favor:
    - Capability match (highest)
    - Resource availability
    - Model already cached
    - Low current load
    """

    def __init__(
        self,
        weight_cpu: float = 1.0,
        weight_memory: float = 1.5,
        weight_gpu: float = 2.0,
        weight_model_cached: float = 3.0,
        weight_load: float = 1.0,
        weight_preference: float = 0.5,
    ):
        self.weights = {
            "cpu": weight_cpu,
            "memory": weight_memory,
            "gpu": weight_gpu,
            "model_cached": weight_model_cached,
            "load": weight_load,
            "preference": weight_preference,
        }

    def score_node(
        self,
        node: NodeResponse,
        task: TaskSubmit,
        current_load: Dict[str, float] = None,
    ) -> ScoreResult:
        """Score a single node for a task."""
        explanation: List[str] = []
        score = 0.0

        # 1. Check basic eligibility
        if node.state != NodeState.ONLINE:
            return ScoreResult(
                node_id=node.node_id,
                hostname=node.hostname,
                score=-1,
                explanation=[f"Node is {node.state}"],
            )

        if NodeRole.CLIENT in node.roles and NodeRole.WORKER not in node.roles:
            return ScoreResult(
                node_id=node.node_id,
                hostname=node.hostname,
                score=-1,
                explanation=["Node is client-only"],
            )

        caps = node.capabilities
        reqs = task.requirements

        # 2. CPU scoring
        if reqs.cpu_threads:
            available_threads = caps.cpu.threads or 0
            if available_threads < reqs.cpu_threads:
                return ScoreResult(
                    node_id=node.node_id,
                    hostname=node.hostname,
                    score=-1,
                    explanation=[f"Insufficient CPU: {available_threads} < {reqs.cpu_threads}"],
                )
            cpu_score = min(1.0, available_threads / (reqs.cpu_threads * 2))
            score += cpu_score * self.weights["cpu"]
            explanation.append(f"CPU: {available_threads} threads available")

        # 3. Memory scoring
        if reqs.memory_gb:
            available_gb = caps.memory.available_bytes / (1024**3)
            if available_gb < reqs.memory_gb:
                return ScoreResult(
                    node_id=node.node_id,
                    hostname=node.hostname,
                    score=-1,
                    explanation=[f"Insufficient RAM: {available_gb:.1f}GB < {reqs.memory_gb}GB"],
                )
            mem_score = min(1.0, available_gb / (reqs.memory_gb * 2))
            score += mem_score * self.weights["memory"]
            explanation.append(f"RAM: {available_gb:.1f}GB available")

        # 4. GPU scoring
        if reqs.gpu_required:
            if not caps.gpus:
                return ScoreResult(
                    node_id=node.node_id,
                    hostname=node.hostname,
                    score=-1,
                    explanation=["GPU required but not available"],
                )

            best_gpu = max(caps.gpus, key=lambda g: g.vram_bytes or 0)
            if reqs.vram_gb:
                available_vram = (best_gpu.vram_bytes or 0) / (1024**3)
                if available_vram < reqs.vram_gb:
                    return ScoreResult(
                        node_id=node.node_id,
                        hostname=node.hostname,
                        score=-1,
                        explanation=[f"Insufficient VRAM: {available_vram:.1f}GB < {reqs.vram_gb}GB"],
                    )
                vram_score = min(1.0, available_vram / (reqs.vram_gb * 2))
                score += vram_score * self.weights["gpu"]
                explanation.append(f"GPU: {best_gpu.model} ({available_vram:.1f}GB VRAM)")

        # 5. Model cached bonus
        if reqs.model_name:
            for provider in caps.providers:
                if reqs.model_name in provider.models:
                    score += self.weights["model_cached"]
                    explanation.append(f"Model '{reqs.model_name}' already cached")
                    break

        # 6. Load penalty (prefer less loaded nodes)
        if current_load and node.node_id in current_load:
            load = current_load[node.node_id]
            load_score = max(0, 1.0 - load) * self.weights["load"]
            score += load_score
            explanation.append(f"Load: {load:.0%}")

        return ScoreResult(
            node_id=node.node_id,
            hostname=node.hostname,
            score=score,
            explanation=explanation,
        )


class Scheduler:
    """
    Central scheduler for task placement.
    
    Uses CapabilityScorer to find the best node for each task.
    """

    def __init__(self, scorer: Optional[CapabilityScorer] = None):
        self.scorer = scorer or CapabilityScorer()

    def select_node(
        self,
        task: TaskSubmit,
        nodes: List[NodeResponse],
        current_load: Optional[Dict[str, float]] = None,
    ) -> Optional[ScoreResult]:
        """
        Select the best node for a task.
        
        Returns None if no suitable node is found.
        """
        if not nodes:
            return None

        results: List[ScoreResult] = []

        for node in nodes:
            result = self.scorer.score_node(node, task, current_load or {})
            if result.score >= 0:
                results.append(result)

        if not results:
            return None

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[0]

    def explain_decision(
        self,
        task: TaskSubmit,
        selected: ScoreResult,
        all_nodes: List[NodeResponse],
    ) -> str:
        """Generate human-readable explanation for scheduler decision."""
        lines = [
            f"Selected Node: {selected.hostname}",
            f"Score: {selected.score:.2f}",
            "Reasons:",
        ]
        for exp in selected.explanation:
            lines.append(f"  - {exp}")

        rejected = [
            n for n in all_nodes
            if n.node_id != selected.node_id
            and n.state == NodeState.ONLINE
        ]
        if rejected:
            lines.append("\nOther nodes considered:")
            for node in rejected:
                result = self.scorer.score_node(node, task)
                if result.score < 0:
                    lines.append(f"  - {node.hostname}: {result.explanation[0]}")
                else:
                    lines.append(f"  - {node.hostname}: score={result.score:.2f}")

        return "\n".join(lines)
