"""
Tests for CortexMesh health monitoring.
"""

import pytest
from datetime import datetime, timezone, timedelta
from cortexmesh.monitor.metrics import MetricsCollector, MetricType
from cortexmesh.monitor.health import (
    HealthMonitor, HealthCheckConfig, Alert, AlertSeverity, AlertStatus
)


class TestAlert:
    def test_create_alert(self):
        alert = Alert(
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="Something happened",
        )
        assert alert.severity == AlertSeverity.WARNING
        assert alert.status == AlertStatus.ACTIVE
        assert alert.title == "Test Alert"

    def test_to_dict(self):
        alert = Alert(
            severity=AlertSeverity.CRITICAL,
            title="Critical Alert",
            message="Critical issue",
            node_id="node-1",
        )
        d = alert.to_dict()
        assert d["severity"] == "critical"
        assert d["status"] == "active"
        assert d["node_id"] == "node-1"


class TestHealthCheckConfig:
    def test_default_config(self):
        config = HealthCheckConfig()
        assert config.cpu_warning_threshold == 80.0
        assert config.cpu_critical_threshold == 95.0
        assert config.node_offline_seconds == 120.0

    def test_custom_config(self):
        config = HealthCheckConfig(cpu_warning_threshold=70.0, cpu_critical_threshold=90.0)
        assert config.cpu_warning_threshold == 70.0
        assert config.cpu_critical_threshold == 90.0


class TestHealthMonitor:
    def test_record_node_heartbeat(self):
        monitor = HealthMonitor()
        monitor.record_node_heartbeat("node-1")
        health = monitor.get_node_health("node-1")
        assert health["state"] == "online"
        assert health["healthy"] is True

    def test_record_node_offline(self):
        monitor = HealthMonitor()
        monitor.record_node_heartbeat("node-1")
        alert = monitor.record_node_offline("node-1")
        
        assert alert is not None
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.node_id == "node-1"
        
        health = monitor.get_node_health("node-1")
        assert health["state"] == "offline"

    def test_node_health_unknown(self):
        monitor = HealthMonitor()
        health = monitor.get_node_health("unknown-node")
        assert health["state"] == "unknown"

    def test_get_node_health_with_metrics(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        
        health = monitor.get_node_health("node-1")
        assert health["cpu_usage"] == 50.0

    def test_check_node_thresholds_cpu_warning(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 85.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        
        alerts = monitor.check_node_thresholds("node-1")
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.WARNING
        assert "CPU" in alerts[0].title

    def test_check_node_thresholds_cpu_critical(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 96.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        
        alerts = monitor.check_node_thresholds("node-1")
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.CRITICAL

    def test_check_node_thresholds_memory_warning(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.MEMORY_USAGE, 85.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        
        alerts = monitor.check_node_thresholds("node-1")
        assert len(alerts) == 1
        assert "Memory" in alerts[0].title

    def test_check_node_thresholds_gpu_critical(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.GPU_USAGE, 99.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        
        alerts = monitor.check_node_thresholds("node-1")
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.CRITICAL
        assert "GPU" in alerts[0].title

    def test_check_node_thresholds_no_data(self):
        metrics = MetricsCollector()
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        
        alerts = monitor.check_node_thresholds("node-1")
        assert len(alerts) == 0

    def test_check_node_thresholds_below_warning(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        
        alerts = monitor.check_node_thresholds("node-1")
        assert len(alerts) == 0

    def test_acknowledge_alert(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 99.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        
        alerts = monitor.check_node_thresholds("node-1")
        alert_id = alerts[0].alert_id
        
        acked = monitor.acknowledge_alert(alert_id, "test-operator")
        assert acked is not None
        assert acked.status == AlertStatus.ACKNOWLEDGED
        assert acked.acknowledged_by == "test-operator"

    def test_acknowledge_nonexistent_alert(self):
        monitor = HealthMonitor()
        result = monitor.acknowledge_alert("fake-id")
        assert result is None

    def test_resolve_alert(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 99.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        
        alerts = monitor.check_node_thresholds("node-1")
        alert_id = alerts[0].alert_id
        
        resolved = monitor.resolve_alert(alert_id)
        assert resolved is not None
        assert resolved.status == AlertStatus.RESOLVED
        assert resolved.resolved_at is not None

    def test_resolve_nonexistent_alert(self):
        monitor = HealthMonitor()
        result = monitor.resolve_alert("fake-id")
        assert result is None

    def test_get_active_alerts(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 99.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        monitor.check_node_thresholds("node-1")
        
        alerts = monitor.get_active_alerts()
        assert len(alerts) == 1

    def test_get_active_alerts_filtered_by_severity(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 99.0)
        metrics.record_sample("node-2", MetricType.CPU_USAGE, 85.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        monitor.record_node_heartbeat("node-2")
        monitor.check_node_thresholds("node-1")
        monitor.check_node_thresholds("node-2")
        
        critical = monitor.get_active_alerts(severity=AlertSeverity.CRITICAL)
        assert len(critical) == 1
        assert critical[0].severity == AlertSeverity.CRITICAL

    def test_get_active_alerts_filtered_by_node(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 99.0)
        metrics.record_sample("node-2", MetricType.CPU_USAGE, 99.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        monitor.record_node_heartbeat("node-2")
        monitor.check_node_thresholds("node-1")
        monitor.check_node_thresholds("node-2")
        
        node1_alerts = monitor.get_active_alerts(node_id="node-1")
        assert len(node1_alerts) == 1

    def test_get_cluster_health(self):
        metrics = MetricsCollector()
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        monitor.record_node_heartbeat("node-2")
        
        health = monitor.get_cluster_health()
        assert health["status"] == "healthy"
        assert health["total_nodes"] == 2
        assert health["online_nodes"] == 2
        assert health["offline_nodes"] == 0

    def test_get_cluster_health_with_offline(self):
        metrics = MetricsCollector()
        monitor = HealthMonitor(metrics, HealthCheckConfig(node_offline_seconds=10))
        monitor.record_node_heartbeat("node-1")
        monitor.record_node_heartbeat("node-2")
        monitor.record_node_offline("node-2")
        
        health = monitor.get_cluster_health()
        # When a node goes offline, a critical alert is created, so status is "critical"
        assert health["status"] == "critical"
        assert health["online_nodes"] == 1
        assert health["offline_nodes"] == 1

    def test_get_cluster_health_critical(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 99.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        monitor.check_node_thresholds("node-1")
        
        health = monitor.get_cluster_health()
        assert health["status"] == "critical"
        assert health["critical_alerts"] == 1

    def test_on_alert_callback(self):
        alerts_received = []
        metrics = MetricsCollector()
        monitor = HealthMonitor(metrics)
        monitor.on_alert(lambda a: alerts_received.append(a))
        
        monitor.record_node_offline("node-1")
        assert len(alerts_received) == 1
        assert alerts_received[0].severity == AlertSeverity.CRITICAL

    def test_alert_cooldown(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 99.0)
        monitor = HealthMonitor(metrics, HealthCheckConfig(alert_cooldown_seconds=60))
        monitor.record_node_heartbeat("node-1")
        
        alerts1 = monitor.check_node_thresholds("node-1")
        alerts2 = monitor.check_node_thresholds("node-1")
        
        # Second call should be blocked by cooldown
        assert len(alerts1) == 1
        assert len(alerts2) == 0

    def test_no_duplicate_active_alerts(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 99.0)
        monitor = HealthMonitor(metrics, HealthCheckConfig(alert_cooldown_seconds=0))
        monitor.record_node_heartbeat("node-1")
        
        alerts1 = monitor.check_node_thresholds("node-1")
        alerts2 = monitor.check_node_thresholds("node-1")
        
        # Should not create duplicate active alert
        assert len(alerts1) == 1
        assert len(alerts2) == 0

    def test_check_all_nodes_detects_offline(self):
        metrics = MetricsCollector()
        config = HealthCheckConfig(node_offline_seconds=0)
        monitor = HealthMonitor(metrics, config)
        
        old_time = datetime.now(timezone.utc) - timedelta(seconds=10)
        monitor._node_last_seen["node-1"] = old_time
        monitor._node_states["node-1"] = "online"
        
        alerts = monitor.check_all_nodes()
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.CRITICAL

    def test_get_all_alerts_with_status_filter(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 99.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        monitor.check_node_thresholds("node-1")
        
        # Get the alert and resolve it
        alerts = monitor.get_active_alerts()
        monitor.resolve_alert(alerts[0].alert_id)
        
        active = monitor.get_all_alerts(status=AlertStatus.ACTIVE)
        resolved = monitor.get_all_alerts(status=AlertStatus.RESOLVED)
        assert len(active) == 0
        assert len(resolved) == 1


class TestHealthMonitorEdgeCases:
    def test_node_health_with_long_offline_duration(self):
        monitor = HealthMonitor()
        old_time = datetime.now(timezone.utc) - timedelta(seconds=300)
        monitor._node_last_seen["node-1"] = old_time
        monitor._node_states["node-1"] = "online"
        
        health = monitor.get_node_health("node-1")
        assert health["offline_duration_seconds"] > 290
        assert health["healthy"] is False

    def test_multiple_alerts_same_node_different_metrics(self):
        metrics = MetricsCollector()
        metrics.record_sample("node-1", MetricType.CPU_USAGE, 99.0)
        metrics.record_sample("node-1", MetricType.MEMORY_USAGE, 99.0)
        monitor = HealthMonitor(metrics)
        monitor.record_node_heartbeat("node-1")
        
        alerts = monitor.check_node_thresholds("node-1")
        assert len(alerts) == 2

    def test_cluster_health_min_nodes(self):
        metrics = MetricsCollector()
        config = HealthCheckConfig(min_nodes_online=5)
        monitor = HealthMonitor(metrics, config)
        monitor.record_node_heartbeat("node-1")
        
        health = monitor.get_cluster_health()
        assert health["status"] == "warning"
