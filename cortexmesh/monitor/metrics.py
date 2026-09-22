"""
CortexMesh — System metrics monitoring.

Tracks CPU, memory, and GPU usage over time for all nodes in the cluster.
Provides aggregation, trend detection, and threshold-based alerting.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional


class MetricType(str, Enum):
    CPU_USAGE = "cpu_usage_percent"
    MEMORY_USAGE = "memory_usage_percent"
    GPU_USAGE = "gpu_usage_percent"
    VRAM_USAGE = "vram_usage_percent"
    DISK_USAGE = "disk_usage_percent"
    NETWORK_IN = "network_in_mbps"
    NETWORK_OUT = "network_out_mbps"
    TASK_COUNT = "task_count"
    TEMPERATURE = "temperature_celsius"


@dataclass
class MetricSample:
    """A single metric data point."""
    sample_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str = ""
    metric_type: MetricType = MetricType.CPU_USAGE
    value: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "sample_id": self.sample_id,
            "node_id": self.node_id,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class MetricSummary:
    """Statistical summary of a metric over time."""
    node_id: str
    metric_type: MetricType
    count: int = 0
    min_value: float = 0.0
    max_value: float = 0.0
    avg_value: float = 0.0
    latest_value: float = 0.0
    latest_timestamp: Optional[datetime] = None
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "metric_type": self.metric_type.value,
            "count": self.count,
            "min": self.min_value,
            "max": self.max_value,
            "avg": round(self.avg_value, 2),
            "latest": self.latest_value,
            "latest_timestamp": self.latest_timestamp.isoformat() if self.latest_timestamp else None,
            "window_start": self.window_start.isoformat() if self.window_start else None,
            "window_end": self.window_end.isoformat() if self.window_end else None,
        }


class MetricsCollector:
    """
    Collects and aggregates system metrics from all nodes.
    
    Supports time-windowed queries, trend detection, and 
    threshold-based alerting.
    """

    def __init__(self, max_history_per_node: int = 10000):
        self._samples: Dict[str, List[MetricSample]] = defaultdict(list)
        self._max_history = max_history_per_node

    def record_sample(
        self,
        node_id: str,
        metric_type: MetricType,
        value: float,
        metadata: Optional[Dict] = None,
    ) -> MetricSample:
        """Record a single metric sample."""
        sample = MetricSample(
            node_id=node_id,
            metric_type=metric_type,
            value=value,
            metadata=metadata or {},
        )
        self._samples[node_id].append(sample)
        
        # Trim history if too large
        if len(self._samples[node_id]) > self._max_history:
            self._samples[node_id] = self._samples[node_id][-self._max_history:]
        
        return sample

    def record_heartbeat_metrics(self, node_id: str, metrics: Dict) -> List[MetricSample]:
        """Record metrics from a node heartbeat."""
        samples = []
        mapping = {
            "cpu_usage_percent": MetricType.CPU_USAGE,
            "memory_usage_percent": MetricType.MEMORY_USAGE,
            "gpu_usage_percent": MetricType.GPU_USAGE,
        }
        for key, metric_type in mapping.items():
            value = metrics.get(key)
            if value is not None:
                sample = self.record_sample(node_id, metric_type, float(value), metrics)
                samples.append(sample)
        return samples

    def get_latest(self, node_id: str, metric_type: MetricType) -> Optional[MetricSample]:
        """Get the latest sample for a node/metric pair."""
        for sample in reversed(self._samples.get(node_id, [])):
            if sample.metric_type == metric_type:
                return sample
        return None

    def get_history(
        self,
        node_id: str,
        metric_type: MetricType,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[MetricSample]:
        """Get metric history for a node."""
        samples = self._samples.get(node_id, [])
        result = [s for s in samples if s.metric_type == metric_type]
        
        if since:
            result = [s for s in result if s.timestamp >= since]
        if until:
            result = [s for s in result if s.timestamp <= until]
        
        return result[-limit:]

    def summarize(
        self,
        node_id: str,
        metric_type: MetricType,
        window_seconds: float = 3600,
    ) -> Optional[MetricSummary]:
        """Compute statistical summary for a metric over a time window."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        samples = self.get_history(node_id, metric_type, since=cutoff)
        
        if not samples:
            return None
        
        values = [s.value for s in samples]
        return MetricSummary(
            node_id=node_id,
            metric_type=metric_type,
            count=len(values),
            min_value=min(values),
            max_value=max(values),
            avg_value=sum(values) / len(values),
            latest_value=samples[-1].value,
            latest_timestamp=samples[-1].timestamp,
            window_start=samples[0].timestamp,
            window_end=samples[-1].timestamp,
        )

    def get_cluster_summary(
        self,
        metric_type: MetricType,
        window_seconds: float = 300,
    ) -> Dict[str, MetricSummary]:
        """Get summary for all nodes."""
        result = {}
        for node_id in self._samples:
            summary = self.summarize(node_id, metric_type, window_seconds)
            if summary:
                result[node_id] = summary
        return result

    def get_all_node_ids(self) -> List[str]:
        """Get all nodes with recorded metrics."""
        return list(self._samples.keys())

    def get_trend(
        self,
        node_id: str,
        metric_type: MetricType,
        window_seconds: float = 300,
    ) -> str:
        """Detect trend: 'rising', 'falling', or 'stable'."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        samples = self.get_history(node_id, metric_type, since=cutoff)
        
        if len(samples) < 3:
            return "insufficient_data"
        
        # Simple linear regression
        half = len(samples) // 2
        first_half = samples[:half]
        second_half = samples[half:]
        
        first_avg = sum(s.value for s in first_half) / len(first_half)
        second_avg = sum(s.value for s in second_half) / len(second_half)
        
        diff = second_avg - first_avg
        if abs(diff) < 2.0:
            return "stable"
        return "rising" if diff > 0 else "falling"

    def clear_node(self, node_id: str) -> int:
        """Clear all metrics for a node. Returns count cleared."""
        count = len(self._samples.get(node_id, []))
        self._samples.pop(node_id, None)
        return count

    def get_cluster_average(self, metric_type: MetricType, window_seconds: float = 300) -> float:
        """Get average value across all nodes."""
        summaries = self.get_cluster_summary(metric_type, window_seconds)
        if not summaries:
            return 0.0
        values = [s.avg_value for s in summaries.values()]
        return sum(values) / len(values)
