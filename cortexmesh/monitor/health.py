"""
CortexMesh — Health monitoring with alerts.

Watches node status, resource usage, and generates alerts when
things go wrong: nodes go offline, usage spikes, lease conflicts.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from cortexmesh.monitor.metrics import MetricsCollector, MetricType


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """A health alert for cluster operators."""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: AlertSeverity = AlertSeverity.WARNING
    status: AlertStatus = AlertStatus.ACTIVE
    title: str = ""
    message: str = ""
    node_id: Optional[str] = None
    metric_type: Optional[str] = None
    threshold_value: float = 0.0
    current_value: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    auto_resolve: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "status": self.status.value,
            "title": self.title,
            "message": self.message,
            "node_id": self.node_id,
            "metric_type": self.metric_type,
            "threshold_value": self.threshold_value,
            "current_value": self.current_value,
            "created_at": self.created_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_by": self.acknowledged_by,
            "auto_resolve": self.auto_resolve,
            "metadata": self.metadata,
        }


@dataclass
class HealthCheckConfig:
    """Configuration for health check thresholds."""
    node_offline_seconds: float = 120.0
    cpu_warning_threshold: float = 80.0
    cpu_critical_threshold: float = 95.0
    memory_warning_threshold: float = 80.0
    memory_critical_threshold: float = 95.0
    gpu_warning_threshold: float = 85.0
    gpu_critical_threshold: float = 98.0
    heartbeat_timeout_seconds: float = 60.0
    min_nodes_online: int = 1
    alert_cooldown_seconds: float = 300.0  # Don't re-alert for same issue


class HealthMonitor:
    """
    Monitors cluster health and generates alerts.
    
    Tracks node connectivity, resource thresholds, and lease conflicts.
    """

    def __init__(
        self,
        metrics_collector: Optional[MetricsCollector] = None,
        config: Optional[HealthCheckConfig] = None,
    ):
        self.metrics = metrics_collector or MetricsCollector()
        self.config = config or HealthCheckConfig()
        self._alerts: Dict[str, Alert] = {}
        self._node_last_seen: Dict[str, datetime] = {}
        self._node_states: Dict[str, str] = {}
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        self._last_alert_time: Dict[str, datetime] = {}  # keyed by (node_id, alert_type)

    def record_node_heartbeat(self, node_id: str, timestamp: Optional[datetime] = None) -> None:
        """Record that a node sent a heartbeat."""
        self._node_last_seen[node_id] = timestamp or datetime.now(timezone.utc)
        self._node_states[node_id] = "online"

    def record_node_offline(self, node_id: str) -> Optional[Alert]:
        """Record a node as offline."""
        self._node_states[node_id] = "offline"
        return self._create_alert(
            severity=AlertSeverity.CRITICAL,
            title=f"Node {node_id} offline",
            message=f"Node {node_id} is no longer reachable.",
            node_id=node_id,
            alert_key=f"{node_id}:offline",
        )

    def get_node_health(self, node_id: str) -> Dict[str, Any]:
        """Get health status for a single node."""
        last_seen = self._node_last_seen.get(node_id)
        state = self._node_states.get(node_id, "unknown")
        
        offline_duration = None
        if last_seen:
            offline_duration = (datetime.now(timezone.utc) - last_seen).total_seconds()
        
        # Get latest metrics
        cpu = self.metrics.get_latest(node_id, MetricType.CPU_USAGE)
        memory = self.metrics.get_latest(node_id, MetricType.MEMORY_USAGE)
        gpu = self.metrics.get_latest(node_id, MetricType.GPU_USAGE)
        
        return {
            "node_id": node_id,
            "state": state,
            "last_seen": last_seen.isoformat() if last_seen else None,
            "offline_duration_seconds": offline_duration,
            "cpu_usage": cpu.value if cpu else None,
            "memory_usage": memory.value if memory else None,
            "gpu_usage": gpu.value if gpu else None,
            "healthy": state == "online" and (offline_duration is None or offline_duration < self.config.heartbeat_timeout_seconds),
        }

    def check_node_thresholds(self, node_id: str) -> List[Alert]:
        """Check resource thresholds for a node. Returns new alerts."""
        alerts = []
        
        checks = [
            (MetricType.CPU_USAGE, self.config.cpu_warning_threshold, self.config.cpu_critical_threshold, "CPU"),
            (MetricType.MEMORY_USAGE, self.config.memory_warning_threshold, self.config.memory_critical_threshold, "Memory"),
            (MetricType.GPU_USAGE, self.config.gpu_warning_threshold, self.config.gpu_critical_threshold, "GPU"),
        ]
        
        for metric_type, warn_thresh, crit_thresh, name in checks:
            latest = self.metrics.get_latest(node_id, metric_type)
            if latest is None:
                continue
            
            value = latest.value
            
            # Check critical threshold
            if value >= crit_thresh:
                alert = self._create_alert(
                    severity=AlertSeverity.CRITICAL,
                    title=f"{name} critical on {node_id}",
                    message=f"{name} usage is {value:.1f}% (threshold: {crit_thresh}%)",
                    node_id=node_id,
                    metric_type=metric_type.value,
                    threshold_value=crit_thresh,
                    current_value=value,
                    alert_key=f"{node_id}:{metric_type.value}:critical",
                )
                if alert:
                    alerts.append(alert)
            
            # Check warning threshold
            elif value >= warn_thresh:
                alert = self._create_alert(
                    severity=AlertSeverity.WARNING,
                    title=f"{name} warning on {node_id}",
                    message=f"{name} usage is {value:.1f}% (threshold: {warn_thresh}%)",
                    node_id=node_id,
                    metric_type=metric_type.value,
                    threshold_value=warn_thresh,
                    current_value=value,
                    alert_key=f"{node_id}:{metric_type.value}:warning",
                )
                if alert:
                    alerts.append(alert)
        
        return alerts

    def check_all_nodes(self) -> List[Alert]:
        """Run health checks on all known nodes."""
        alerts = []
        now = datetime.now(timezone.utc)
        
        for node_id, last_seen in self._node_last_seen.items():
            offline_duration = (now - last_seen).total_seconds()
            
            if offline_duration > self.config.node_offline_seconds:
                if self._node_states.get(node_id) != "offline":
                    alert = self.record_node_offline(node_id)
                    if alert:
                        alerts.append(alert)
            elif offline_duration > self.config.heartbeat_timeout_seconds:
                # Node might be degraded
                alert = self._create_alert(
                    severity=AlertSeverity.WARNING,
                    title=f"Node {node_id} heartbeat delayed",
                    message=f"Last heartbeat was {offline_duration:.0f}s ago.",
                    node_id=node_id,
                    alert_key=f"{node_id}:delayed",
                )
                if alert:
                    alerts.append(alert)
            
            # Check thresholds
            threshold_alerts = self.check_node_thresholds(node_id)
            alerts.extend(threshold_alerts)
        
        return alerts

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "operator") -> Optional[Alert]:
        """Acknowledge an alert."""
        alert = self._alerts.get(alert_id)
        if not alert or alert.status != AlertStatus.ACTIVE:
            return None
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = acknowledged_by
        return alert

    def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """Resolve an alert."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
        return alert

    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        node_id: Optional[str] = None,
    ) -> List[Alert]:
        """Get active alerts, optionally filtered."""
        alerts = [a for a in self._alerts.values() if a.status == AlertStatus.ACTIVE]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if node_id:
            alerts = [a for a in alerts if a.node_id == node_id]
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)

    def get_all_alerts(
        self,
        status: Optional[AlertStatus] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """Get all alerts, optionally filtered by status."""
        alerts = list(self._alerts.values())
        if status:
            alerts = [a for a in alerts if a.status == status]
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)[:limit]

    def get_cluster_health(self) -> Dict[str, Any]:
        """Get overall cluster health status."""
        total_nodes = len(self._node_last_seen)
        online_nodes = sum(1 for s in self._node_states.values() if s == "online")
        offline_nodes = total_nodes - online_nodes
        active_alerts = self.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        
        status = "healthy"
        if critical_alerts:
            status = "critical"
        elif offline_nodes > 0:
            status = "degraded"
        elif online_nodes < self.config.min_nodes_online:
            status = "warning"
        
        return {
            "status": status,
            "total_nodes": total_nodes,
            "online_nodes": online_nodes,
            "offline_nodes": offline_nodes,
            "active_alerts": len(active_alerts),
            "critical_alerts": len(critical_alerts),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def on_alert(self, callback: Callable[[Alert], None]) -> None:
        """Register a callback for new alerts."""
        self._alert_callbacks.append(callback)

    def _create_alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        node_id: Optional[str] = None,
        metric_type: Optional[str] = None,
        threshold_value: float = 0.0,
        current_value: float = 0.0,
        alert_key: str = "",
        auto_resolve: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Alert]:
        """Create an alert, respecting cooldown."""
        # Check cooldown
        now = datetime.now(timezone.utc)
        last_time = self._last_alert_time.get(alert_key)
        if last_time and (now - last_time).total_seconds() < self.config.alert_cooldown_seconds:
            return None
        
        # Check if there's already an active alert for this key
        for alert in self._alerts.values():
            if alert.status == AlertStatus.ACTIVE and alert.metadata.get("alert_key") == alert_key:
                return None
        
        self._last_alert_time[alert_key] = now
        
        alert = Alert(
            severity=severity,
            title=title,
            message=message,
            node_id=node_id,
           metric_type=metric_type,
            threshold_value=threshold_value,
            current_value=current_value,
            auto_resolve=auto_resolve,
            metadata={"alert_key": alert_key, **(metadata or {})},
        )
        self._alerts[alert.alert_id] = alert
        
        # Notify callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass
        
        return alert
