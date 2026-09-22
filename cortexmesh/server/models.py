"""
CortexMesh — Server-side model management.

Provides API-level model operations: list, stage, sync, delete.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class ModelState(str, Enum):
    AVAILABLE = "available"
    STAGING = "staging"
    SYNCING = "syncing"
    DELETING = "deleting"
    ERROR = "error"


@dataclass
class ManagedModel:
    """A model tracked by the controller."""
    model_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    provider_type: str = "ollama"
    endpoint: Optional[str] = None
    size_bytes: int = 0
    context_length: int = 4096
    requires_gpu: bool = False
    vram_gb: float = 0.0
    state: ModelState = ModelState.AVAILABLE
    staged_node_ids: List[str] = field(default_factory=list)
    available_node_ids: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "provider_type": self.provider_type,
            "endpoint": self.endpoint,
            "size_bytes": self.size_bytes,
            "context_length": self.context_length,
            "requires_gpu": self.requires_gpu,
            "vram_gb": self.vram_gb,
            "state": self.state.value,
            "staged_node_ids": self.staged_node_ids,
            "available_node_ids": self.available_node_ids,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ModelManager:
    """
    Manages AI models across the cluster.
    
    Tracks which models are available on which nodes,
    and provides staging/sync operations.
    """

    def __init__(self):
        self._models: Dict[str, ManagedModel] = {}

    def register_model(
        self,
        name: str,
        provider_type: str = "ollama",
        endpoint: Optional[str] = None,
        size_bytes: int = 0,
        context_length: int = 4096,
        requires_gpu: bool = False,
        vram_gb: float = 0.0,
        metadata: Optional[Dict] = None,
    ) -> ManagedModel:
        """Register a new model or update existing one."""
        # Check if already registered
        for model in self._models.values():
            if model.name == name and model.provider_type == provider_type:
                # Update existing
                if endpoint:
                    model.endpoint = endpoint
                if size_bytes:
                    model.size_bytes = size_bytes
                model.context_length = context_length
                model.requires_gpu = requires_gpu
                model.vram_gb = vram_gb
                if metadata:
                    model.metadata.update(metadata)
                model.updated_at = datetime.now(timezone.utc)
                return model
        
        model = ManagedModel(
            name=name,
            provider_type=provider_type,
            endpoint=endpoint,
            size_bytes=size_bytes,
            context_length=context_length,
            requires_gpu=requires_gpu,
            vram_gb=vram_gb,
            metadata=metadata or {},
        )
        self._models[model.model_id] = model
        return model

    def list_models(
        self,
        provider_type: Optional[str] = None,
        state: Optional[ModelState] = None,
        requires_gpu: Optional[bool] = None,
    ) -> List[ManagedModel]:
        """List models with optional filtering."""
        models = list(self._models.values())
        if provider_type:
            models = [m for m in models if m.provider_type == provider_type]
        if state:
            models = [m for m in models if m.state == state]
        if requires_gpu is not None:
            models = [m for m in models if m.requires_gpu == requires_gpu]
        return models

    def get_model(self, model_id: str) -> Optional[ManagedModel]:
        """Get a model by ID."""
        return self._models.get(model_id)

    def get_model_by_name(self, name: str) -> Optional[ManagedModel]:
        """Get a model by name."""
        for model in self._models.values():
            if model.name == name:
                return model
        return None

    def stage_model(self, model_id: str, node_ids: List[str]) -> Optional[ManagedModel]:
        """
        Stage a model on specified nodes.
        
        This is a controller-side tracking operation; the actual model
        download/pull happens asynchronously via the agent.
        """
        model = self._models.get(model_id)
        if not model:
            return None
        
        model.state = ModelState.STAGING
        model.staged_node_ids = list(set(model.staged_node_ids + node_ids))
        model.updated_at = datetime.now(timezone.utc)
        return model

    def sync_model(self, model_id: str, source_node_id: str, target_node_ids: List[str]) -> Optional[ManagedModel]:
        """Sync a model from source node to target nodes."""
        model = self._models.get(model_id)
        if not model:
            return None
        
        model.state = ModelState.SYNCING
        model.staged_node_ids = list(set(model.staged_node_ids + target_node_ids))
        model.updated_at = datetime.now(timezone.utc)
        return model

    def mark_model_available(self, model_id: str, node_id: str) -> Optional[ManagedModel]:
        """Mark a model as available on a node."""
        model = self._models.get(model_id)
        if not model:
            return None
        
        if node_id not in model.available_node_ids:
            model.available_node_ids.append(node_id)
        
        # If all staged nodes now have it, set to available
        if model.state in (ModelState.STAGING, ModelState.SYNCING):
            staged_set = set(model.staged_node_ids)
            available_set = set(model.available_node_ids)
            if staged_set.issubset(available_set):
                model.state = ModelState.AVAILABLE
        
        model.updated_at = datetime.now(timezone.utc)
        return model

    def remove_model_from_node(self, model_id: str, node_id: str) -> Optional[ManagedModel]:
        """Remove a model's availability from a specific node."""
        model = self._models.get(model_id)
        if not model:
            return None
        
        if node_id in model.available_node_ids:
            model.available_node_ids.remove(node_id)
        if node_id in model.staged_node_ids:
            model.staged_node_ids.remove(node_id)
        
        model.updated_at = datetime.now(timezone.utc)
        return model

    def delete_model(self, model_id: str) -> bool:
        """Delete a model from tracking."""
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False

    def discover_models_from_nodes(self, nodes: List[Dict]) -> List[ManagedModel]:
        """Discover and register models from node capabilities."""
        discovered = []
        for node in nodes:
            node_id = node.get("node_id", "")
            providers = node.get("capabilities", {}).get("providers", [])
            for provider in providers:
                provider_type = provider.get("provider_type", "ollama")
                endpoint = provider.get("endpoint")
                for model_name in provider.get("models", []):
                    model = self.register_model(
                        name=model_name,
                        provider_type=provider_type,
                        endpoint=endpoint,
                    )
                    if node_id and node_id not in model.available_node_ids:
                        model.available_node_ids.append(node_id)
                        model.updated_at = datetime.now(timezone.utc)
                    if model not in discovered:
                        discovered.append(model)
        return discovered

    def get_models_on_node(self, node_id: str) -> List[ManagedModel]:
        """Get all models available on a specific node."""
        return [m for m in self._models.values() if node_id in m.available_node_ids]

    def get_stats(self) -> Dict:
        """Get model management statistics."""
        total = len(self._models)
        states = {}
        for m in self._models.values():
            states[m.state.value] = states.get(m.state.value, 0) + 1
        
        total_size = sum(m.size_bytes for m in self._models.values())
        gpu_models = sum(1 for m in self._models.values() if m.requires_gpu)
        
        return {
            "total_models": total,
            "by_state": states,
            "total_size_bytes": total_size,
            "gpu_models": gpu_models,
        }
