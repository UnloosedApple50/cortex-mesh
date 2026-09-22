"""
Tests for CortexMesh model management.
"""

import pytest
from cortexmesh.server.models import ManagedModel, ModelManager, ModelState


class TestManagedModel:
    def test_create_model(self):
        model = ManagedModel(
            name="llama3",
            provider_type="ollama",
            size_bytes=4 * 1024**3,
            context_length=4096,
        )
        assert model.name == "llama3"
        assert model.state == ModelState.AVAILABLE
        assert model.model_id is not None

    def test_create_model_gpu(self):
        model = ManagedModel(
            name="mixtral",
            requires_gpu=True,
            vram_gb=24.0,
        )
        assert model.requires_gpu is True
        assert model.vram_gb == 24.0

    def test_to_dict(self):
        model = ManagedModel(name="test", provider_type="ollama")
        d = model.to_dict()
        assert d["name"] == "test"
        assert d["provider_type"] == "ollama"
        assert "model_id" in d
        assert "created_at" in d


class TestModelManager:
    def test_register_model(self):
        manager = ModelManager()
        model = manager.register_model(
            name="llama3",
            provider_type="ollama",
            endpoint="http://localhost:11434",
        )
        assert model.name == "llama3"
        assert model.endpoint == "http://localhost:11434"

    def test_register_model_updates_existing(self):
        manager = ModelManager()
        model1 = manager.register_model(name="llama3", provider_type="ollama")
        model2 = manager.register_model(
            name="llama3",
            provider_type="ollama",
            endpoint="http://new:11434",
        )
        assert model1.model_id == model2.model_id
        assert model2.endpoint == "http://new:11434"

    def test_list_models(self):
        manager = ModelManager()
        manager.register_model(name="model1", provider_type="ollama")
        manager.register_model(name="model2", provider_type="vllm")
        
        models = manager.list_models()
        assert len(models) == 2

    def test_list_models_filter_provider(self):
        manager = ModelManager()
        manager.register_model(name="model1", provider_type="ollama")
        manager.register_model(name="model2", provider_type="vllm")
        
        ollama_models = manager.list_models(provider_type="ollama")
        assert len(ollama_models) == 1
        assert ollama_models[0].provider_type == "ollama"

    def test_list_models_filter_gpu(self):
        manager = ModelManager()
        manager.register_model(name="small", requires_gpu=False)
        manager.register_model(name="large", requires_gpu=True, vram_gb=24)
        
        gpu_models = manager.list_models(requires_gpu=True)
        assert len(gpu_models) == 1
        assert gpu_models[0].name == "large"

    def test_get_model(self):
        manager = ModelManager()
        registered = manager.register_model(name="test")
        retrieved = manager.get_model(registered.model_id)
        
        assert retrieved is not None
        assert retrieved.model_id == registered.model_id

    def test_get_model_not_found(self):
        manager = ModelManager()
        assert manager.get_model("nonexistent") is None

    def test_get_model_by_name(self):
        manager = ModelManager()
        manager.register_model(name="llama3")
        model = manager.get_model_by_name("llama3")
        assert model is not None
        assert model.name == "llama3"

    def test_get_model_by_name_not_found(self):
        manager = ModelManager()
        assert manager.get_model_by_name("nonexistent") is None

    def test_stage_model(self):
        manager = ModelManager()
        model = manager.register_model(name="test")
        staged = manager.stage_model(model.model_id, ["node-1", "node-2"])
        
        assert staged is not None
        assert staged.state == ModelState.STAGING
        assert "node-1" in staged.staged_node_ids
        assert "node-2" in staged.staged_node_ids

    def test_stage_model_not_found(self):
        manager = ModelManager()
        assert manager.stage_model("nonexistent", ["node-1"]) is None

    def test_sync_model(self):
        manager = ModelManager()
        model = manager.register_model(name="test")
        synced = manager.sync_model(model.model_id, "source-node", ["target-1", "target-2"])
        
        assert synced is not None
        assert synced.state == ModelState.SYNCING
        assert "target-1" in synced.staged_node_ids

    def test_sync_model_not_found(self):
        manager = ModelManager()
        assert manager.sync_model("nonexistent", "src", ["tgt"]) is None

    def test_mark_model_available(self):
        manager = ModelManager()
        model = manager.register_model(name="test")
        manager.stage_model(model.model_id, ["node-1"])
        updated = manager.mark_model_available(model.model_id, "node-1")
        
        assert updated is not None
        assert "node-1" in updated.available_node_ids
        assert updated.state == ModelState.AVAILABLE

    def test_mark_model_available_partial(self):
        manager = ModelManager()
        model = manager.register_model(name="test")
        manager.stage_model(model.model_id, ["node-1", "node-2"])
        updated = manager.mark_model_available(model.model_id, "node-1")
        
        assert updated.state == ModelState.STAGING  # Still staging until all nodes

    def test_remove_model_from_node(self):
        manager = ModelManager()
        model = manager.register_model(name="test")
        model.available_node_ids = ["node-1", "node-2"]
        
        updated = manager.remove_model_from_node(model.model_id, "node-1")
        assert updated is not None
        assert "node-1" not in updated.available_node_ids
        assert "node-2" in updated.available_node_ids

    def test_delete_model(self):
        manager = ModelManager()
        model = manager.register_model(name="test")
        result = manager.delete_model(model.model_id)
        assert result is True
        assert manager.get_model(model.model_id) is None

    def test_delete_model_not_found(self):
        manager = ModelManager()
        result = manager.delete_model("nonexistent")
        assert result is False

    def test_discover_models_from_nodes(self):
        manager = ModelManager()
        nodes = [
            {
                "node_id": "node-1",
                "capabilities": {
                    "providers": [
                        {
                            "provider_type": "ollama",
                            "endpoint": "http://localhost:11434",
                            "models": ["llama3", "mistral"],
                        }
                    ]
                },
            },
            {
                "node_id": "node-2",
                "capabilities": {
                    "providers": [
                        {
                            "provider_type": "ollama",
                            "endpoint": "http://remote:11434",
                            "models": ["llama3", "codellama"],
                        }
                    ]
                },
            },
        ]
        
        discovered = manager.discover_models_from_nodes(nodes)
        assert len(discovered) >= 3
        
        llama = manager.get_model_by_name("llama3")
        assert llama is not None
        assert "node-1" in llama.available_node_ids
        assert "node-2" in llama.available_node_ids

    def test_get_models_on_node(self):
        manager = ModelManager()
        model1 = manager.register_model(name="model1")
        model2 = manager.register_model(name="model2")
        model1.available_node_ids = ["node-1"]
        model2.available_node_ids = ["node-1", "node-2"]
        
        node1_models = manager.get_models_on_node("node-1")
        assert len(node1_models) == 2

    def test_get_stats(self):
        manager = ModelManager()
        manager.register_model(name="small", size_bytes=4 * 1024**3)
        manager.register_model(name="large", size_bytes=40 * 1024**3, requires_gpu=True)
        
        stats = manager.get_stats()
        assert stats["total_models"] == 2
        assert stats["total_size_bytes"] == 44 * 1024**3
        assert stats["gpu_models"] == 1

    def test_get_stats_with_state_filter(self):
        manager = ModelManager()
        model = manager.register_model(name="test")
        manager.stage_model(model.model_id, ["node-1"])
        
        stats = manager.get_stats()
        assert "staging" in stats["by_state"]


class TestModelManagerEdgeCases:
    def test_discover_models_no_providers(self):
        manager = ModelManager()
        nodes = [{"node_id": "node-1", "capabilities": {}}]
        discovered = manager.discover_models_from_nodes(nodes)
        assert len(discovered) == 0

    def test_discover_models_no_models(self):
        manager = ModelManager()
        nodes = [
            {
                "node_id": "node-1",
                "capabilities": {
                    "providers": [{"provider_type": "ollama", "models": []}]
                },
            }
        ]
        discovered = manager.discover_models_from_nodes(nodes)
        assert len(discovered) == 0

    def test_stage_model_deduplicates_node_ids(self):
        manager = ModelManager()
        model = manager.register_model(name="test")
        manager.stage_model(model.model_id, ["node-1"])
        manager.stage_model(model.model_id, ["node-1", "node-2"])
        
        updated = manager.get_model(model.model_id)
        assert updated is not None
        assert updated.staged_node_ids.count("node-1") == 1
        assert "node-2" in updated.staged_node_ids
