"""
Persistent Semantic Memory & User Preferences for Veni AI.

Upgraded to use Vector Database (ChromaDB) for long-term RAG context.
Learns from user interactions and remembers:
- Coding style preferences
- Framework/library choices
- Common corrections
- Project-specific notes
"""

import json
import logging
import time
import uuid
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("veni.memory")

_SEMANTIC_DEPS: tuple[Any | None, Any | None] | None = None


def _load_semantic_dependencies() -> tuple[Any | None, Any | None]:
    """Load optional semantic-memory dependencies lazily."""
    global _SEMANTIC_DEPS
    if _SEMANTIC_DEPS is not None:
        return _SEMANTIC_DEPS

    try:
        chromadb_module = import_module("chromadb")
        sentence_transformers_module = import_module("sentence_transformers")
        sentence_transformer_cls = sentence_transformers_module.SentenceTransformer
        _SEMANTIC_DEPS = (chromadb_module, sentence_transformer_cls)
    except Exception:
        _SEMANTIC_DEPS = (None, None)

    return _SEMANTIC_DEPS


class MemoryEntry:
    """A single memory entry with metadata."""

    def __init__(
        self,
        category: str,
        content: str,
        weight: float = 1.0,
        timestamp: Optional[float] = None,
    ):
        self.category = category
        self.content = content
        self.weight = weight
        self.timestamp = timestamp or time.time()
        self.access_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "content": self.content,
            "weight": self.weight,
            "timestamp": self.timestamp,
            "access_count": self.access_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        entry = cls(
            category=data["category"],
            content=data["content"],
            weight=data.get("weight", 1.0),
            timestamp=data.get("timestamp"),
        )
        entry.access_count = data.get("access_count", 0)
        return entry


class MemorySystem:
    """
    Persistent semantic memory using ChromaDB for RAG.
    """

    # Maximum number of semantic memory entries before oldest are evicted
    MAX_ENTRIES = 2000

    def __init__(
        self, memory_dir: Optional[Path] = None, enable_semantic: bool = False
    ):
        self.memory_dir = memory_dir or Path.home() / ".veni-chatbot" / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self._preferences: Dict[str, Any] = {}
        self._corrections: List[str] = []
        self._project_notes: Dict[str, str] = {}

        # Vector DB components
        self.chroma_client = None
        self.collection = None
        self.model = None
        self._model_load_attempted = False
        self._semantic_model_name = "all-MiniLM-L6-v2"
        self.semantic_enabled = enable_semantic

        # Legacy paths
        self._preferences_path = self.memory_dir / "preferences.json"
        self._corrections_path = self.memory_dir / "corrections.json"
        self._project_notes_path = self.memory_dir / "project_notes.json"

        if self.semantic_enabled:
            self._init_vector_db()
        self._load_legacy()

    def _init_vector_db(self):
        """Initialize ChromaDB and SentenceTransformer."""
        self.semantic_enabled = True
        chromadb_module, sentence_transformer_cls = _load_semantic_dependencies()
        if chromadb_module is None or sentence_transformer_cls is None:
            logger.warning(
                "ChromaDB or SentenceTransformer not installed. Using legacy memory only."
            )
            return

        try:
            self.chroma_client = chromadb_module.PersistentClient(
                path=str(self.memory_dir / "chroma")
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name="veni_memories"
            )
            logger.info(
                "Semantic memory initialized with ChromaDB (lazy model loading)."
            )
        except Exception as e:
            logger.error("Failed to initialize vector DB: %s", e)

    def _ensure_model(self):
        """Load the embedding model on first semantic memory operation."""
        if self.model is not None:
            return self.model
        if self._model_load_attempted:
            return None
        self._model_load_attempted = True
        _, sentence_transformer_cls = _load_semantic_dependencies()
        if sentence_transformer_cls is None:
            return None

        try:
            self.model = sentence_transformer_cls(self._semantic_model_name)
            logger.info("Semantic embedding model loaded: %s", self._semantic_model_name)
        except Exception as e:
            logger.error("Failed to load embedding model: %s", e)
            self.model = None

        return self.model

    def _load_legacy(self):
        """Load JSON-based components."""
        if self._preferences_path.exists():
            try:
                self._preferences = json.loads(self._preferences_path.read_text(encoding="utf-8"))
            except Exception:
                self._preferences = {}

        if self._corrections_path.exists():
            try:
                self._corrections = json.loads(self._corrections_path.read_text(encoding="utf-8"))
            except Exception:
                self._corrections = []

        if self._project_notes_path.exists():
            try:
                self._project_notes = json.loads(self._project_notes_path.read_text(encoding="utf-8"))
            except Exception:
                self._project_notes = {}

    def _save_legacy(self):
        """Save JSON-based components."""
        self._preferences_path.write_text(
            json.dumps(self._preferences, indent=2), encoding="utf-8"
        )
        self._corrections_path.write_text(
            json.dumps(self._corrections, indent=2), encoding="utf-8"
        )
        self._project_notes_path.write_text(
            json.dumps(self._project_notes, indent=2), encoding="utf-8"
        )

    # --- Public API ---

    def remember(self, category: str, content: str, weight: float = 1.0):
        """Add a new memory entry to vector DB."""
        if not self.collection:
            return

        model = self._ensure_model()
        if model is None:
            return

        try:
            embedding = model.encode(content).tolist()
            self.collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=[embedding],
                metadatas=[
                    {"category": category, "weight": weight, "timestamp": time.time()}
                ],
                documents=[content],
            )
            logger.info("Remembered semantically: %s", content[:50])
            self._evict_if_needed()
        except Exception as e:
            logger.error("Failed to store semantic memory: %s", e)

    def _evict_if_needed(self) -> None:
        """Evict the oldest entries when collection exceeds MAX_ENTRIES."""
        if not self.collection:
            return
        try:
            count = self.collection.count()
            if count <= self.MAX_ENTRIES:
                return
            overflow = count - self.MAX_ENTRIES
            # Fetch all IDs + metadata, sort by timestamp, delete oldest
            results = self.collection.get(include=["metadatas"])
            ids = results.get("ids", [])
            metadatas = results.get("metadatas", [])
            if not ids:
                return
            # Pair each id with its timestamp, sort ascending (oldest first)
            pairs = sorted(
                zip(ids, metadatas),
                key=lambda x: x[1].get("timestamp", 0) if x[1] else 0,
            )
            ids_to_delete = [pair[0] for pair in pairs[:overflow]]
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info("Evicted %d old memory entries.", len(ids_to_delete))
        except Exception as e:
            logger.warning("Memory eviction failed: %s", e)

    def recall(self, query: str, limit: int = 5, category: Optional[str] = None) -> List[str]:
        """Retrieve semantically relevant memories via RAG, optionally filtered by category."""
        if not self.collection:
            return []

        model = self._ensure_model()
        if model is None:
            return []

        try:
            embedding = model.encode(query).tolist()
            where = {"category": category} if category else None
            results = self.collection.query(
                query_embeddings=[embedding], 
                n_results=limit,
                where=where
            )
            return results.get("documents", [[]])[0]
        except Exception as e:
            logger.error("Failed to recall semantic memory: %s", e)
        return []

    def set_preference(self, key: str, value: Any):
        self._preferences[key] = value
        self._save_legacy()

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self._preferences.get(key, default)

    def record_correction(self, pattern: str):
        if pattern not in self._corrections:
            self._corrections.append(pattern)
            self._save_legacy()
            self.remember("correction", f"Avoid pattern: {pattern}")

    def set_project_note(self, project_path: str, note: str):
        self._project_notes[project_path] = note
        self._save_legacy()
        self.remember("project_note", f"Note for {project_path}: {note}")

    def get_context_prompt(self, current_query: Optional[str] = None) -> str:
        """Build a personalized system prompt from memories (semantic + static)."""
        parts = []

        # 1. Semantic Recall (RAG)
        if current_query:
            relevant = self.recall(current_query)
            if relevant:
                rag_text = "Relevant Context from Memory:\n"
                for i, r in enumerate(relevant, 1):
                    rag_text += f"{i}. {r}\n"
                parts.append(rag_text)

        # 2. User preferences (Static)
        if self._preferences:
            pref_text = "User Preferences:\n"
            for key, value in sorted(self._preferences.items()):
                pref_text += f"- {key}: {value}\n"
            parts.append(pref_text)

        # 3. Corrections (Static)
        if self._corrections:
            corr_text = "Patterns to Avoid:\n"
            for c in self._corrections[-5:]:
                corr_text += f"- {c}\n"
            parts.append(corr_text)

        return "\n".join(parts) if parts else ""

    def get_stats(self) -> Dict[str, int]:
        count = self.collection.count() if self.collection else 0
        return {
            "total_memories": count + len(self._preferences) + len(self._corrections),
            "semantic_memories": count,
            "preferences": len(self._preferences),
            "corrections": len(self._corrections),
            "project_notes": len(self._project_notes),
        }

    def clear(self):
        """Clear all memory data."""
        self._preferences.clear()
        self._corrections.clear()
        self._project_notes.clear()
        self._save_legacy()
        if self.chroma_client:
            self.chroma_client.delete_collection("veni_memories")
            self.collection = self.chroma_client.create_collection("veni_memories")
