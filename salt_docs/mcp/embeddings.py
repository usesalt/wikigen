"""Local embedding generation for semantic search.

This module provides local embedding generation using sentence-transformers
for privacy-preserving semantic search without API calls.
"""

from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer


# Global model cache to avoid reloading
_embedding_model: Optional[SentenceTransformer] = None


def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Load the embedding model (cached globally).

    Args:
        model_name: Name of the sentence-transformers model to use

    Returns:
        Loaded SentenceTransformer model
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


def get_embedding(text: str, model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """
    Generate embedding for a single text.

    Args:
        text: Text to embed
        model_name: Name of the sentence-transformers model to use

    Returns:
        NumPy array of the embedding vector
    """
    model = load_embedding_model(model_name)
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding


def get_embeddings_batch(
    texts: List[str], model_name: str = "all-MiniLM-L6-v2", batch_size: int = 32
) -> np.ndarray:
    """
    Generate embeddings for a batch of texts (more efficient).

    Args:
        texts: List of texts to embed
        model_name: Name of the sentence-transformers model to use
        batch_size: Batch size for processing

    Returns:
        NumPy array of shape (len(texts), embedding_dim) containing embeddings
    """
    if not texts:
        return np.array([])

    model = load_embedding_model(model_name)
    embeddings = model.encode(
        texts, convert_to_numpy=True, batch_size=batch_size, show_progress_bar=False
    )
    return embeddings
