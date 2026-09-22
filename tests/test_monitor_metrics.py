"""
Tests for CortexMesh metrics monitoring.
"""

import pytest
from datetime import datetime, timezone, timedelta
from cortexmesh.monitor.metrics import MetricsCollector, MetricSample, MetricType


class TestMetricSample:
    def test_create_sample(self):
        sample = MetricSample(
            node_id="node-1",
            metric_type=MetricType.CPU_USAGE,
            value=75.5,
        )
        assert sample.node_id == "node-1"
        assert sample.metric_type == MetricType.CPU_USAGE
        assert sample.value == 75.5
        assert sample.sample_id is not None

    def test_to_dict(self):
        sample = MetricSample(
            node_id="node-1",
            metric_type=MetricType.MEMORY_USAGE,
            value=60.0,
        )
        d = sample.to_dict()
        assert d["node_id"] == "node-1"
        assert d["metric_type"] == "memory_usage_percent"
        assert d["value"] == 60.0
        assert "sample_id" in d
        assert "timestamp" in d

    def test_sample_with_metadata(self):
        sample = MetricSample(
            node_id="node-1",
            metric_type=MetricType.CPU_USAGE,
            value=50.0,
            metadata={"source": "heartbeat"},
        )
        assert sample.metadata["source"] == "heartbeat"


class TestMetricsCollector:
    def test_record_sample(self):
        collector = MetricsCollector()
        sample = collector.record_sample("node-1", MetricType.CPU_USAGE, 75.0)
        assert sample.node_id == "node-1"
        assert sample.value == 75.0

    def test_record_heartbeat_metrics(self):
        collector = MetricsCollector()
        samples = collector.record_heartbeat_metrics("node-1", {
            "cpu_usage_percent": 50.0,
            "memory_usage_percent": 60.0,
            "gpu_usage_percent": 70.0,
        })
        assert len(samples) == 3
        cpu_samples = [s for s in samples if s.metric_type == MetricType.CPU_USAGE]
        assert len(cpu_samples) == 1
        assert cpu_samples[0].value == 50.0

    def test_record_heartbeat_metrics_partial(self):
        collector = MetricsCollector()
        samples = collector.record_heartbeat_metrics("node-1", {
            "cpu_usage_percent": 50.0,
        })
        assert len(samples) == 1

    def test_record_heartbeat_metrics_none_values(self):
        collector = MetricsCollector()
        samples = collector.record_heartbeat_metrics("node-1", {
            "cpu_usage_percent": None,
            "memory_usage_percent": 60.0,
        })
        assert len(samples) == 1

    def test_get_latest(self):
        collector = MetricsCollector()
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 75.0)
        
        latest = collector.get_latest("node-1", MetricType.CPU_USAGE)
        assert latest is not None
        assert latest.value == 75.0

    def test_get_latest_empty(self):
        collector = MetricsCollector()
        latest = collector.get_latest("node-1", MetricType.CPU_USAGE)
        assert latest is None

    def test_get_history(self):
        collector = MetricsCollector()
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 60.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 70.0)
        
        history = collector.get_history("node-1", MetricType.CPU_USAGE)
        assert len(history) == 3

    def test_get_history_with_limit(self):
        collector = MetricsCollector()
        for i in range(10):
            collector.record_sample("node-1", MetricType.CPU_USAGE, float(i))
        
        history = collector.get_history("node-1", MetricType.CPU_USAGE, limit=5)
        assert len(history) == 5

    def test_summarize(self):
        collector = MetricsCollector()
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 60.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 70.0)
        
        summary = collector.summarize("node-1", MetricType.CPU_USAGE)
        assert summary is not None
        assert summary.count == 3
        assert summary.min_value == 50.0
        assert summary.max_value == 70.0
        assert summary.avg_value == 60.0
        assert summary.latest_value == 70.0

    def test_summarize_empty(self):
        collector = MetricsCollector()
        summary = collector.summarize("node-1", MetricType.CPU_USAGE)
        assert summary is None

    def test_get_cluster_summary(self):
        collector = MetricsCollector()
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        collector.record_sample("node-2", MetricType.CPU_USAGE, 70.0)
        
        summaries = collector.get_cluster_summary(MetricType.CPU_USAGE)
        assert len(summaries) == 2
        assert "node-1" in summaries
        assert "node-2" in summaries

    def test_get_all_node_ids(self):
        collector = MetricsCollector()
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        collector.record_sample("node-2", MetricType.CPU_USAGE, 70.0)
        
        ids = collector.get_all_node_ids()
        assert len(ids) == 2
        assert "node-1" in ids
        assert "node-2" in ids

    def test_get_trend_rising(self):
        collector = MetricsCollector()
        collector.record_sample("node-1", MetricType.CPU_USAGE, 30.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 70.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 90.0)
        
        trend = collector.get_trend("node-1", MetricType.CPU_USAGE)
        assert trend == "rising"

    def test_get_trend_falling(self):
        collector = MetricsCollector()
        collector.record_sample("node-1", MetricType.CPU_USAGE, 90.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 70.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 30.0)
        
        trend = collector.get_trend("node-1", MetricType.CPU_USAGE)
        assert trend == "falling"

    def test_get_trend_stable(self):
        collector = MetricsCollector()
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 51.0)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.5)
        collector.record_sample("node-1", MetricType.CPU_USAGE, 49.5)
        
        trend = collector.get_trend("node-1", MetricType.CPU_USAGE)
        assert trend == "stable"

    def test_get_trend_insufficient_data(self):
        collector = MetricsCollector()
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        
        trend = collector.get_trend("node-1", MetricType.CPU_USAGE)
        assert trend == "insufficient_data"

    def test_clear_node(self):
        collector = MetricsCollector()
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        collector.record_sample("node-1", MetricType.MEMORY_USAGE, 60.0)
        
        count = collector.clear_node("node-1")
        assert count == 2
        assert collector.get_latest("node-1", MetricType.CPU_USAGE) is None

    def test_get_cluster_average(self):
        collector = MetricsCollector()
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        collector.record_sample("node-2", MetricType.CPU_USAGE, 70.0)
        
        avg = collector.get_cluster_average(MetricType.CPU_USAGE)
        assert avg == 60.0

    def test_get_cluster_average_empty(self):
        collector = MetricsCollector()
        avg = collector.get_cluster_average(MetricType.CPU_USAGE)
        assert avg == 0.0


class TestMetricsCollectorEdgeCases:
    def test_history_trimming(self):
        collector = MetricsCollector(max_history_per_node=5)
        for i in range(10):
            collector.record_sample("node-1", MetricType.CPU_USAGE, float(i))
        
        history = collector.get_history("node-1", MetricType.CPU_USAGE)
        assert len(history) == 5

    def test_multiple_metric_types_separate(self):
        collector = MetricsCollector()
        collector.record_sample("node-1", MetricType.CPU_USAGE, 50.0)
        collector.record_sample("node-1", MetricType.MEMORY_USAGE, 60.0)
        
        cpu_history = collector.get_history("node-1", MetricType.CPU_USAGE)
        mem_history = collector.get_history("node-1", MetricType.MEMORY_USAGE)
        assert len(cpu_history) == 1
        assert len(mem_history) == 1

    def test_get_history_with_time_window(self):
        collector = MetricsCollector()
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        new_time = datetime.now(timezone.utc)
        
        sample1 = MetricSample(
            node_id="node-1",
            metric_type=MetricType.CPU_USAGE,
            value=50.0,
            timestamp=old_time,
        )
        sample2 = MetricSample(
            node_id="node-1",
            metric_type=MetricType.CPU_USAGE,
            value=75.0,
            timestamp=new_time,
        )
        collector._samples["node-1"] = [sample1, sample2]
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        history = collector.get_history("node-1", MetricType.CPU_USAGE, since=cutoff)
        assert len(history) == 1
        assert history[0].value == 75.0
