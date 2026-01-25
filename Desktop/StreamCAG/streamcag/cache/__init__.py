import hashlib
import json
import pickle
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class CacheEntry:
    """Represents a single entry in the semantic cache."""

    id: str
    text: str
    embedding: np.ndarray
    metadata: Dict
    timestamp: float
    access_count: int = 0
    last_accessed: float = 0.0


class SemanticCache:
    """L1 Cache: In-memory semantic cache with intelligent eviction policies."""

    def __init__(
        self,
        max_size: int = 100,
        embedding_model: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.7,
    ):
        self.max_size = max_size
        self.embedding_model = SentenceTransformer(embedding_model)
        self.similarity_threshold = similarity_threshold

        # Core storage structures
        self.entries: Dict[str, CacheEntry] = OrderedDict()
        self.index = None  # FAISS index for fast similarity search
        self.id_to_index = {}  # Map cache ID to FAISS index position

        # Statistics
        self.hits = 0
        self.misses = 0

    def _create_index(self, dimension: int):
        """Create a new FAISS index."""
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity

    def add(self, text: str, metadata: Optional[Dict] = None) -> str:
        """Add text to cache with automatic embedding."""
        # Generate unique ID for the entry
        entry_id = hashlib.md5(text.encode()).hexdigest()[:16]

        # Skip if already in cache
        if entry_id in self.entries:
            return entry_id

        # Create embedding
        embedding = self.embedding_model.encode([text])[0]
        embedding = embedding / np.linalg.norm(embedding)  # Normalize

        # Create entry
        entry = CacheEntry(
            id=entry_id,
            text=text,
            embedding=embedding,
            metadata=metadata or {},
            timestamp=time.time(),
        )

        # Manage cache size
        if len(self.entries) >= self.max_size:
            self._evict_entries()

        # Add to storage
        self.entries[entry_id] = entry

        # Update FAISS index
        if self.index is None:
            self._create_index(len(embedding))

        self.index.add(np.array([embedding]).astype("float32"))
        self.id_to_index[entry_id] = len(self.entries) - 1

        return entry_id

    def search(self, query: str, k: int = 5) -> List[Tuple[CacheEntry, float]]:
        """Search for similar entries in cache."""
        query_embedding = self.embedding_model.encode([query])[0]
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        if self.index is None or len(self.entries) == 0:
            self.misses += 1
            return []

        # Search in FAISS index
        distances, indices = self.index.search(
            np.array([query_embedding]).astype("float32"), min(k, len(self.entries))
        )

        # Get entries and update access stats
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx != -1:  # Valid index
                # Find entry by index
                for entry_id, entry_index in self.id_to_index.items():
                    if entry_index == idx:
                        entry = self.entries[entry_id]
                        entry.access_count += 1
                        entry.last_accessed = time.time()

                        if distance >= self.similarity_threshold:
                            self.hits += 1
                            results.append((entry, float(distance)))
                        else:
                            self.misses += 1
                        break

        return results

    def _evict_entries(self):
        """Intelligent cache eviction based on multiple policies."""
        if len(self.entries) == 0:
            return

        # Combine scores from different eviction policies
        scores = []
        current_time = time.time()

        for entry_id, entry in self.entries.items():
            # LRU score (higher is better to keep)
            lru_score = (
                entry.last_accessed / current_time if entry.last_accessed > 0 else 0
            )

            # Frequency score
            freq_score = entry.access_count / max(
                1, sum(e.access_count for e in self.entries.values())
            )

            # Recency score (time since last access)
            recency_score = 1.0 / (current_time - entry.last_accessed + 1)

            # Combined score (lower = more likely to evict)
            combined_score = 0.4 * lru_score + 0.4 * freq_score + 0.2 * recency_score
            scores.append((entry_id, combined_score))

        # Sort by score (lowest first) and remove the lowest scoring entries
        scores.sort(key=lambda x: x[1])
        num_to_remove = max(1, len(self.entries) - self.max_size // 2)

        for entry_id, _ in scores[:num_to_remove]:
            self._remove_entry(entry_id)

    def _remove_entry(self, entry_id: str):
        """Remove a specific entry from cache."""
        if entry_id in self.entries:
            # Remove from index mapping
            if entry_id in self.id_to_index:
                del self.id_to_index[entry_id]

            # Remove from entries
            del self.entries[entry_id]

            # Rebuild index for simplicity (could be optimized)
            self._rebuild_index()

    def _rebuild_index(self):
        """Rebuild the FAISS index from current entries."""
        if len(self.entries) == 0:
            self.index = None
            self.id_to_index = {}
            return

        embeddings = []
        self.id_to_index = {}

        for idx, (entry_id, entry) in enumerate(self.entries.items()):
            embeddings.append(entry.embedding)
            self.id_to_index[entry_id] = idx

        self._create_index(embeddings[0].shape[0])
        self.index.add(np.array(embeddings).astype("float32"))

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "size": len(self.entries),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / max(1, self.hits + self.misses),
            "avg_access_count": np.mean([e.access_count for e in self.entries.values()])
            if self.entries
            else 0,
        }


class PersistentCache(SemanticCache):
    """L2 Cache: Persistent semantic cache with disk storage."""

    def __init__(self, storage_path: str = "./cache_data", **kwargs):
        super().__init__(**kwargs)
        self.storage_path = storage_path
        self.index_path = f"{storage_path}/faiss.index"
        self.metadata_path = f"{storage_path}/metadata.pkl"

        # Load existing cache if available
        self._load_from_disk()

    def _load_from_disk(self):
        """Load cache data from disk."""
        import os
        import pickle

        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, "rb") as f:
                    data = pickle.load(f)
                    self.entries = data.get("entries", OrderedDict())
                    self.id_to_index = data.get("id_to_index", {})
                    self.hits = data.get("hits", 0)
                    self.misses = data.get("misses", 0)

                if os.path.exists(self.index_path):
                    self.index = faiss.read_index(self.index_path)

                print(f"Loaded persistent cache with {len(self.entries)} entries")
            except Exception as e:
                print(f"Error loading cache: {e}")
                self.entries = OrderedDict()
                self.id_to_index = {}

    def save(self):
        """Save cache to disk."""
        import os
        import pickle

        os.makedirs(self.storage_path, exist_ok=True)

        # Save FAISS index
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)

        # Save metadata
        data = {
            "entries": self.entries,
            "id_to_index": self.id_to_index,
            "hits": self.hits,
            "misses": self.misses,
        }

        with open(self.metadata_path, "wb") as f:
            pickle.dump(data, f)

        print(f"Persistent cache saved with {len(self.entries)} entries")

    def add(self, text: str, metadata: Optional[Dict] = None) -> str:
        """Add entry with automatic persistence."""
        entry_id = super().add(text, metadata)
        self.save()  # Auto-save on addition
        return entry_id
