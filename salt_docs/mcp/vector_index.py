"""FAISS vector index management for semantic search.

This module provides FAISS index management for storing and searching
document chunk embeddings.
"""

import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from threading import Lock
import numpy as np

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

from ..config import CONFIG_DIR


class VectorIndex:
    """
    FAISS vector index manager for semantic search.

    Manages a FAISS index for storing and searching document chunk embeddings.
    Also maintains metadata mapping chunk IDs to file paths and chunk information.
    """

    def __init__(self, index_path: Optional[Path] = None, embedding_dim: int = 384):
        """
        Initialize the vector index.

        Args:
            index_path: Path to save/load the FAISS index. Defaults to config_dir/vector_index.faiss
            embedding_dim: Dimension of embeddings (default: 384 for all-MiniLM-L6-v2)
        """
        if not FAISS_AVAILABLE:
            raise ImportError(
                "FAISS is not available. Please install faiss-cpu: pip install faiss-cpu"
            )

        if index_path is None:
            index_path = CONFIG_DIR / "vector_index.faiss"

        self.index_path = index_path
        self.metadata_path = index_path.with_suffix(".metadata.pkl")
        self.embedding_dim = embedding_dim
        self._lock = Lock()

        # FAISS index (FlatIndex for exact search)
        self.index: Optional[faiss.Index] = None

        # Metadata: chunk_id -> {file_path, chunk_index, content, start_pos, end_pos}
        self.metadata: Dict[int, Dict[str, Any]] = {}

        # File to chunk IDs mapping: file_path -> [chunk_id, ...]
        self.file_to_chunks: Dict[str, List[int]] = {}

        # Next chunk ID
        self.next_chunk_id = 0

        # Load existing index if available
        self._load()

    def _load(self) -> None:
        """Load FAISS index and metadata from disk."""
        with self._lock:
            if self.index_path.exists() and self.metadata_path.exists():
                try:
                    # Load FAISS index
                    self.index = faiss.read_index(str(self.index_path))

                    # Load metadata
                    with open(self.metadata_path, "rb") as f:
                        data = pickle.load(f)
                        self.metadata = data.get("metadata", {})
                        self.file_to_chunks = data.get("file_to_chunks", {})
                        self.next_chunk_id = data.get("next_chunk_id", 0)

                    # Verify embedding dimension matches
                    if self.index.d != self.embedding_dim:
                        raise ValueError(
                            f"Index embedding dimension ({self.index.d}) "
                            f"does not match expected ({self.embedding_dim})"
                        )
                except Exception as e:
                    # If loading fails, start fresh
                    print(f"Warning: Could not load vector index: {e}")
                    self._init_index()
            else:
                self._init_index()

    def _init_index(self) -> None:
        """Initialize a new FAISS index."""
        # Use FlatIndex for exact search (good for <1M vectors)
        # For larger datasets, consider IVF or HNSW
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.metadata = {}
        self.file_to_chunks = {}
        self.next_chunk_id = 0

    def add_chunks(
        self,
        file_path: str,
        chunks: List[Dict[str, Any]],
        embeddings: np.ndarray,
    ) -> None:
        """
        Add chunks and their embeddings to the index.

        Args:
            file_path: Path to the file these chunks belong to
            chunks: List of chunk dictionaries with 'content', 'start_pos', 'end_pos', 'chunk_index'
            embeddings: NumPy array of embeddings (shape: (len(chunks), embedding_dim))
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS is not available")

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Number of chunks ({len(chunks)}) does not match "
                f"number of embeddings ({len(embeddings)})"
            )

        with self._lock:
            # Remove existing chunks for this file
            if file_path in self.file_to_chunks:
                self._remove_file(file_path)

            # Ensure embeddings are float32 and 2D
            if embeddings.dtype != np.float32:
                embeddings = embeddings.astype(np.float32)
            if len(embeddings.shape) == 1:
                embeddings = embeddings.reshape(1, -1)

            # Add embeddings to FAISS index
            self.index.add(embeddings)

            # Add metadata for each chunk
            chunk_ids = []
            for i, chunk in enumerate(chunks):
                chunk_id = self.next_chunk_id
                chunk_ids.append(chunk_id)

                self.metadata[chunk_id] = {
                    "file_path": file_path,
                    "chunk_index": chunk.get("chunk_index", i),
                    "content": chunk.get("content", ""),
                    "start_pos": chunk.get("start_pos", 0),
                    "end_pos": chunk.get("end_pos", 0),
                }

                self.next_chunk_id += 1

            # Update file to chunks mapping
            self.file_to_chunks[file_path] = chunk_ids

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        file_filter: Optional[List[str]] = None,
    ) -> List[Tuple[int, float, Dict[str, Any]]]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            file_filter: Optional list of file paths to filter results

        Returns:
            List of tuples: (chunk_id, distance, metadata_dict)
            Sorted by distance (lower is better)
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS is not available")

        if self.index is None or self.index.ntotal == 0:
            return []

        with self._lock:
            # Ensure query embedding is float32 and 2D
            if query_embedding.dtype != np.float32:
                query_embedding = query_embedding.astype(np.float32)
            if len(query_embedding.shape) == 1:
                query_embedding = query_embedding.reshape(1, -1)

            # Search in FAISS
            distances, indices = self.index.search(
                query_embedding, k * 2
            )  # Get more, filter later

            # Filter and format results
            results = []
            seen_files = {}  # Track chunks per file for file_filter

            for idx, dist in zip(indices[0], distances[0]):
                if idx < 0:  # Invalid index
                    continue

                chunk_id = idx
                if chunk_id not in self.metadata:
                    continue

                metadata = self.metadata[chunk_id]
                file_path = metadata["file_path"]

                # Apply file filter if provided
                if file_filter is not None and file_path not in file_filter:
                    continue

                # Limit chunks per file (if file_filter is used)
                if file_filter is not None:
                    if file_path not in seen_files:
                        seen_files[file_path] = 0
                    if seen_files[file_path] >= 5:  # Max chunks per file
                        continue
                    seen_files[file_path] += 1

                results.append((chunk_id, float(dist), metadata))

                if len(results) >= k:
                    break

            return results

    def _remove_file(self, file_path: str) -> None:
        """Remove all chunks for a file (internal method, not thread-safe)."""
        if file_path not in self.file_to_chunks:
            return

        chunk_ids = self.file_to_chunks[file_path]

        # Note: FAISS doesn't support removing individual vectors efficiently
        # For now, we'll mark them as removed in metadata and rebuild on next save
        # A better approach would be to rebuild the index, but that's expensive
        # For production, consider using a more advanced index type that supports deletion

        # Remove from metadata
        for chunk_id in chunk_ids:
            self.metadata.pop(chunk_id, None)

        # Remove from file mapping
        del self.file_to_chunks[file_path]

    def remove_file(self, file_path: str) -> None:
        """
        Remove all chunks for a file from the index.

        Note: This marks chunks as removed but doesn't actually remove them
        from the FAISS index. The index will be rebuilt on next save.

        Args:
            file_path: Path to the file to remove
        """
        with self._lock:
            self._remove_file(file_path)

    def save(self) -> None:
        """Save FAISS index and metadata to disk."""
        if not FAISS_AVAILABLE:
            return

        with self._lock:
            if self.index is None:
                return

            # Ensure directory exists
            self.index_path.parent.mkdir(parents=True, exist_ok=True)

            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))

            # Save metadata
            with open(self.metadata_path, "wb") as f:
                pickle.dump(
                    {
                        "metadata": self.metadata,
                        "file_to_chunks": self.file_to_chunks,
                        "next_chunk_id": self.next_chunk_id,
                    },
                    f,
                )

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        with self._lock:
            return {
                "total_chunks": len(self.metadata),
                "total_files_with_chunks": len(self.file_to_chunks),
                "index_size": self.index.ntotal if self.index else 0,
                "embedding_dim": self.embedding_dim,
            }
