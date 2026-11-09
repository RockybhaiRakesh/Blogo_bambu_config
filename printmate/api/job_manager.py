"""
Thread-safe Model Repository and Job Manager for PRINTMATE AI API.
Maintains isolated workspaces, cached analyses, and progress tracking.
"""

import os
import shutil
import uuid
import time
from typing import Dict, Any, Optional, List
from threading import Lock

from printmate.core.config import Config

class JobManager:
    """Manages active models, isolated workspaces, and cached pipeline results."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(JobManager, cls).__new__(cls)
                cls._instance._init_manager()
            return cls._instance

    def _init_manager(self):
        self.workspace_base = os.path.join(Config.WORKSPACE_DIR, "outputs", "api_workspace")
        os.makedirs(self.workspace_base, exist_ok=True)
        self.models_registry: Dict[str, Dict[str, Any]] = {}
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.split_cache: Dict[str, Dict[str, Any]] = {}
        self.split_rec_cache: Dict[str, Dict[str, Any]] = {}
        self.paint_rec_cache: Dict[str, Dict[str, Any]] = {}
        self.settings_cache: Dict[str, Dict[str, Any]] = {}
        self.mesh_cache: Dict[str, Any] = {}
        self._scan_preloaded_models()

    def _scan_preloaded_models(self):
        """Scans only user-uploaded models in the workspace to remember active uploads across restarts."""
        if os.path.exists(self.workspace_base):
            for model_id in os.listdir(self.workspace_base):
                m_dir = os.path.join(self.workspace_base, model_id)
                if os.path.isdir(m_dir):
                    for f in os.listdir(m_dir):
                        ext = os.path.splitext(f)[1].lower()
                        if ext in [".stl", ".obj", ".3mf"] and not f.startswith("preview_") and "part" not in f.lower():
                            full_p = os.path.join(m_dir, f)
                            if model_id not in self.models_registry and os.path.exists(full_p):
                                self.models_registry[model_id] = {
                                    "model_id": model_id,
                                    "filename": f,
                                    "file_path": os.path.abspath(full_p),
                                    "file_size_bytes": os.path.getsize(full_p),
                                    "format": ext.lstrip("."),
                                    "is_split_part": False,
                                    "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(full_p)))
                                }

    def register_uploaded_model(self, file_content: bytes, original_filename: str) -> Dict[str, Any]:
        """Saves an uploaded file to an isolated directory and indexes it."""
        model_id = str(uuid.uuid4())[:12]
        ext = os.path.splitext(original_filename)[1].lower()
        model_dir = os.path.join(self.workspace_base, model_id)
        os.makedirs(model_dir, exist_ok=True)

        target_path = os.path.join(model_dir, original_filename)
        with open(target_path, "wb") as f:
            f.write(file_content)

        meta = {
            "model_id": model_id,
            "filename": original_filename,
            "file_path": os.path.abspath(target_path),
            "file_size_bytes": len(file_content),
            "format": ext.lstrip("."),
            "is_split_part": False,
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with self._lock:
            self.models_registry[model_id] = meta
        return meta

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if model_id in self.models_registry:
                return self.models_registry[model_id]
            # Dynamic fallback: check disk if folder exists in workspace_base
            m_dir = os.path.join(self.workspace_base, model_id)
            if os.path.isdir(m_dir):
                for f in os.listdir(m_dir):
                    ext = os.path.splitext(f)[1].lower()
                    if ext in [".stl", ".obj", ".3mf"] and not f.startswith("preview_"):
                        full_p = os.path.join(m_dir, f)
                        meta = {
                            "model_id": model_id,
                            "filename": f,
                            "file_path": os.path.abspath(full_p),
                            "file_size_bytes": os.path.getsize(full_p),
                            "format": ext.lstrip("."),
                            "is_split_part": False,
                            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(full_p)))
                        }
                        self.models_registry[model_id] = meta
                        return meta
            return None

    def list_models(self) -> List[Dict[str, Any]]:
        with self._lock:
            self._scan_preloaded_models()
            return list(self.models_registry.values())

    def get_cached_analysis(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if model_id in self.analysis_cache:
                return self.analysis_cache[model_id]
            m = self.models_registry.get(model_id)
            if m:
                cache_file = os.path.join(os.path.dirname(m["file_path"]), "analysis_cache.json")
                if os.path.exists(cache_file):
                    try:
                        import json
                        with open(cache_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            self.analysis_cache[model_id] = data
                            return data
                    except Exception:
                        pass
            return None

    def set_cached_analysis(self, model_id: str, data: Dict[str, Any]):
        with self._lock:
            self.analysis_cache[model_id] = data
            m = self.models_registry.get(model_id)
            if m:
                cache_file = os.path.join(os.path.dirname(m["file_path"]), "analysis_cache.json")
                try:
                    import json
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                except Exception:
                    pass

    def get_cached_split(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if model_id in self.split_cache:
                return self.split_cache[model_id]
            m = self.models_registry.get(model_id)
            if m:
                cache_file = os.path.join(os.path.dirname(m["file_path"]), "split_cache.json")
                if os.path.exists(cache_file):
                    try:
                        import json
                        with open(cache_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            self.split_cache[model_id] = data
                            return data
                    except Exception:
                        pass
            return None

    def set_cached_split(self, model_id: str, data: Dict[str, Any]):
        with self._lock:
            self.split_cache[model_id] = data
            m = self.models_registry.get(model_id)
            if m:
                cache_file = os.path.join(os.path.dirname(m["file_path"]), "split_cache.json")
                try:
                    import json
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                except Exception:
                    pass

    def get_cached_split_recommendation(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.split_rec_cache.get(model_id)

    def set_cached_split_recommendation(self, model_id: str, data: Dict[str, Any]):
        with self._lock:
            self.split_rec_cache[model_id] = data

    def get_cached_paint_recommendation(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.paint_rec_cache.get(model_id)

    def set_cached_paint_recommendation(self, model_id: str, data: Dict[str, Any]):
        with self._lock:
            self.paint_rec_cache[model_id] = data

    def get_cached_mesh(self, model_id: str) -> Any:
        with self._lock:
            return self.mesh_cache.get(model_id)

    def set_cached_mesh(self, model_id: str, mesh: Any):
        with self._lock:
            if len(self.mesh_cache) > 6:
                oldest_key = next(iter(self.mesh_cache))
                del self.mesh_cache[oldest_key]
            self.mesh_cache[model_id] = mesh

