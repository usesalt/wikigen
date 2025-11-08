"""Fast file indexing system using SQLite FTS for machine-wide markdown search.

This module provides indexed search capabilities across multiple directories using
SQLite FTS5 for full-text search of file paths, names, and resource names.
Also supports semantic search using FAISS for chunk-based retrieval.
"""

import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from threading import Lock
import hashlib

from ..config import CONFIG_DIR
from ..defaults import DEFAULT_CONFIG
from .chunking import chunk_markdown
from .embeddings import get_embeddings_batch
from .vector_index import VectorIndex


class FileIndexer:
    """
    Fast file indexer using SQLite FTS5 for efficient full-text search.

    Indexes markdown files across configured directories and provides
    fast search capabilities through SQLite's full-text search engine.
    Also supports semantic search using FAISS for chunk-based retrieval.
    """

    def __init__(
        self,
        index_db_path: Optional[Path] = None,
        enable_semantic_search: Optional[bool] = None,
        vector_index_path: Optional[Path] = None,
    ):
        """
        Initialize the file indexer.

        Args:
            index_db_path: Path to SQLite database. Defaults to config_dir/file_index.db
            enable_semantic_search: Enable semantic search. Defaults to config value.
            vector_index_path: Path to FAISS vector index. Defaults to config_dir/vector_index.faiss
        """
        if index_db_path is None:
            index_db_path = CONFIG_DIR / "file_index.db"

        self.db_path = index_db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

        # Load semantic search config
        if enable_semantic_search is None:
            config = DEFAULT_CONFIG.copy()
            enable_semantic_search = config.get("semantic_search_enabled", True)

        self.enable_semantic_search = enable_semantic_search

        # Initialize vector index if semantic search is enabled
        self.vector_index: Optional[VectorIndex] = None
        if self.enable_semantic_search:
            try:
                # Get embedding model dimension (384 for all-MiniLM-L6-v2)
                embedding_model = DEFAULT_CONFIG.get(
                    "embedding_model", "all-MiniLM-L6-v2"
                )
                embedding_dim = 384  # all-MiniLM-L6-v2 dimension
                self.vector_index = VectorIndex(
                    embedding_dim=embedding_dim, index_path=vector_index_path
                )
            except ImportError:
                # FAISS not available, disable semantic search
                self.enable_semantic_search = False
                self.vector_index = None

        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with FTS5 table for full-text search."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.cursor()

                # Create main files table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL UNIQUE,
                        file_name TEXT NOT NULL,
                        resource_name TEXT NOT NULL,
                        directory TEXT NOT NULL,
                        size INTEGER,
                        modified_time REAL,
                        indexed_time REAL NOT NULL,
                        content_hash TEXT
                    )
                """
                )

                # Create indexes separately
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_file_path ON files(file_path)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_file_name ON files(file_name)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_directory ON files(directory)"
                )

                # Create FTS5 virtual table for full-text search
                # FTS5 allows fast full-text search on multiple columns
                cursor.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                        file_path,
                        file_name,
                        resource_name,
                        directory,
                        content='files',
                        content_rowid='id'
                    )
                """
                )

                # Create triggers to keep FTS5 in syncdex with main table
                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
                        INSERT INTO files_fts(rowid, file_path, file_name, resource_name, directory)
                        VALUES (new.id, new.file_path, new.file_name, new.resource_name, new.directory);
                    END
                """
                )

                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
                        INSERT INTO files_fts(files_fts, rowid, file_path, file_name, resource_name, directory)
                        VALUES('delete', old.id, old.file_path, old.file_name, old.resource_name, old.directory);
                    END
                """
                )

                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
                        INSERT INTO files_fts(files_fts, rowid, file_path, file_name, resource_name, directory)
                        VALUES('delete', old.id, old.file_path, old.file_name, old.resource_name, old.directory);
                        INSERT INTO files_fts(rowid, file_path, file_name, resource_name, directory)
                        VALUES (new.id, new.file_path, new.file_name, new.resource_name, new.directory);
                    END
                """
                )

                # Migration: Populate FTS5 from existing files if needed
                cursor.execute(
                    """
                    INSERT INTO files_fts(rowid, file_path, file_name, resource_name, directory)
                    SELECT id, file_path, file_name, resource_name, directory
                    FROM files
                    WHERE NOT EXISTS (
                        SELECT 1 FROM files_fts WHERE files_fts.rowid = files.id
                    )
                """
                )

                conn.commit()
            finally:
                conn.close()

    def _calculate_content_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content for change detection."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def index_directory(
        self,
        directory: Path,
        pattern: str = "*.md",
        exclude_hidden: bool = True,
        max_depth: Optional[int] = None,
    ) -> Tuple[int, int, int]:
        """
        Index all markdown files in a directory recursively.

        Args:
            directory: Directory to index
            pattern: File pattern to match (default: "*.md")
            exclude_hidden: Skip hidden files/directories
            max_depth: Maximum recursion depth (None = unlimited)

        Returns:
            Tuple of (files_added, files_updated, files_skipped)
        """
        if not directory.exists() or not directory.is_dir():
            return (0, 0, 0)

        files_added = 0
        files_updated = 0
        files_skipped = 0
        indexed_time = time.time()

        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.cursor()

                # Find all matching files
                for md_file in directory.rglob(pattern):
                    # Skip if exceeds max_depth
                    if max_depth is not None:
                        depth = len(md_file.relative_to(directory).parts) - 1
                        if depth > max_depth:
                            continue

                    # Skip hidden files/directories
                    if exclude_hidden:
                        relative_path = md_file.relative_to(directory)
                        if any(
                            part.startswith(".") for part in relative_path.parts[:-1]
                        ):
                            continue

                    try:
                        # Get file metadata
                        stat = md_file.stat()
                        file_size = stat.st_size
                        modified_time = stat.st_mtime

                        # Calculate resource name (path without extension)
                        try:
                            relative_path = md_file.relative_to(directory)
                        except ValueError:
                            # File not relative to directory (shouldn't happen)
                            files_skipped += 1
                            continue

                        resource_name = str(relative_path.with_suffix(""))
                        file_name = md_file.name
                        file_dir = str(md_file.parent)
                        file_path_str = str(md_file.absolute())

                        # Calculate content hash
                        content_hash = self._calculate_content_hash(md_file)

                        # Check if file already indexed
                        cursor.execute(
                            "SELECT id, content_hash, modified_time FROM files WHERE file_path = ?",
                            (file_path_str,),
                        )
                        existing = cursor.fetchone()

                        file_changed = False
                        if existing:
                            file_id, old_hash, old_mtime = existing
                            # Update if file changed
                            if content_hash != old_hash or modified_time > old_mtime:
                                cursor.execute(
                                    """
                                    UPDATE files
                                    SET file_name = ?, resource_name = ?, directory = ?,
                                        size = ?, modified_time = ?, indexed_time = ?,
                                        content_hash = ?
                                    WHERE id = ?
                                """,
                                    (
                                        file_name,
                                        resource_name,
                                        file_dir,
                                        file_size,
                                        modified_time,
                                        indexed_time,
                                        content_hash,
                                        file_id,
                                    ),
                                )
                                files_updated += 1
                                file_changed = True
                            else:
                                files_skipped += 1
                        else:
                            # Insert new file
                            cursor.execute(
                                """
                                INSERT INTO files (
                                    file_path, file_name, resource_name, directory,
                                    size, modified_time, indexed_time, content_hash
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    file_path_str,
                                    file_name,
                                    resource_name,
                                    file_dir,
                                    file_size,
                                    modified_time,
                                    indexed_time,
                                    content_hash,
                                ),
                            )
                            files_added += 1
                            file_changed = True

                        # Index chunks for semantic search if enabled and file changed
                        if (
                            self.enable_semantic_search
                            and self.vector_index
                            and file_changed
                        ):
                            try:
                                self._index_file_chunks(md_file, file_path_str)
                            except Exception as e:
                                # Log error but don't fail indexing
                                print(
                                    f"Warning: Could not index chunks for {file_path_str}: {e}"
                                )

                    except Exception:
                        # Skip files we can't read or process
                        files_skipped += 1
                        continue

                conn.commit()
            finally:
                conn.close()

            # Save vector index after indexing
            if self.enable_semantic_search and self.vector_index:
                try:
                    self.vector_index.save()
                except Exception as e:
                    print(f"Warning: Could not save vector index: {e}")

        return (files_added, files_updated, files_skipped)

    def _index_file_chunks(self, file_path: Path, file_path_str: str) -> None:
        """
        Index chunks for a file in the vector index.

        Args:
            file_path: Path to the file
            file_path_str: String representation of the file path
        """
        if not self.vector_index:
            return

        try:
            # Read file content
            content = file_path.read_text(encoding="utf-8")

            # Get chunking config
            config = DEFAULT_CONFIG.copy()
            chunk_size = config.get("chunk_size", 500)
            chunk_overlap = config.get("chunk_overlap", 50)

            # Chunk the content
            chunks = chunk_markdown(
                content, chunk_size=chunk_size, overlap=chunk_overlap
            )

            if not chunks:
                return

            # Generate embeddings for chunks
            chunk_texts = [chunk["content"] for chunk in chunks]
            embedding_model = config.get("embedding_model", "all-MiniLM-L6-v2")
            embeddings = get_embeddings_batch(chunk_texts, model_name=embedding_model)

            # Add chunks to vector index
            self.vector_index.add_chunks(file_path_str, chunks, embeddings)
        except Exception as e:
            # Log error but don't fail
            print(f"Warning: Could not index chunks for {file_path_str}: {e}")

    def search(
        self, query: str, limit: int = 50, directory_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for files using full-text search.

        Args:
            query: Search query (supports FTS5 syntax)
            limit: Maximum number of results
            directory_filter: Optional directory path to filter results

        Returns:
            List of dictionaries with file information
        """
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Build FTS5 query
                # Handle empty query
                if not query or not query.strip():
                    fts_query = "*"  # Match all
                else:
                    # Escape FTS5 special characters
                    # FTS5 special characters: " ' \ and operators: AND OR NOT
                    # For simplicity, we'll use a simple word search
                    def escape_fts5_token(word):
                        # Remove FTS5 special characters that cause syntax errors
                        # Replace with space to split into multiple tokens
                        word = (
                            word.replace('"', " ").replace("'", " ").replace("\\", " ")
                        )
                        word = word.replace("(", " ").replace(")", " ")
                        word = word.replace("[", " ").replace("]", " ")
                        word = word.replace("?", " ")  # Remove question marks
                        word = word.replace("-", " ")  # Split hyphenated words
                        # Remove extra spaces
                        word = " ".join(word.split())
                        return word

                    # Split query into words and escape each
                    words = query.strip().split()
                    escaped_words = []
                    for word in words:
                        word = word.strip()
                        if word:
                            # Escape special characters
                            escaped = escape_fts5_token(word)
                            if escaped:  # Only add if word is not empty after escaping
                                # Split if multiple words after escaping
                                for token in escaped.split():
                                    if token:
                                        # Use prefix matching (*) to match partial tokens
                                        # Remove any existing * to avoid double wildcards
                                        token = token.rstrip("*")
                                        escaped_words.append(f"{token}*")

                    # If no valid words after escaping, use wildcard
                    if not escaped_words:
                        fts_query = "*"
                    else:
                        # Join with OR for any-word matching
                        fts_query = " OR ".join(escaped_words)

                # Build SQL query
                # Note: FTS5 MATCH doesn't support parameterized queries in some SQLite versions
                # We embed the query directly after proper escaping
                # Escape single quotes in fts_query for SQL embedding
                fts_query_escaped = fts_query.replace("'", "''")

                if directory_filter:
                    sql = f"""
                        SELECT f.id, f.file_path, f.file_name, f.resource_name,
                               f.directory, f.size, f.modified_time
                        FROM files_fts
                        JOIN files f ON files_fts.rowid = f.id
                        WHERE files_fts MATCH '{fts_query_escaped}' AND f.directory LIKE ?
                        ORDER BY files_fts.rank
                        LIMIT ?
                    """
                    cursor.execute(sql, (f"%{directory_filter}%", limit))
                else:
                    sql = f"""
                        SELECT f.id, f.file_path, f.file_name, f.resource_name,
                               f.directory, f.size, f.modified_time
                        FROM files_fts
                        JOIN files f ON files_fts.rowid = f.id
                        WHERE files_fts MATCH '{fts_query_escaped}'
                        ORDER BY files_fts.rank
                        LIMIT ?
                    """
                    cursor.execute(sql, (limit,))

                results = []
                rows = cursor.fetchall()
                for row in rows:
                    results.append(
                        {
                            "id": row["id"],
                            "file_path": row["file_path"],
                            "file_name": row["file_name"],
                            "resource_name": row["resource_name"],
                            "directory": row["directory"],
                            "size": row["size"],
                            "modified_time": row["modified_time"],
                        }
                    )

                # Fallback: if FTS returns no matches, try LIKE on filenames/paths
                if not results and query and query.strip():
                    like = f"%{query.strip()}%"
                    if directory_filter:
                        cursor.execute(
                            """
                            SELECT id, file_path, file_name, resource_name,
                                   directory, size, modified_time
                            FROM files
                            WHERE (file_name LIKE ? OR file_path LIKE ?)
                              AND directory LIKE ?
                            LIMIT ?
                            """,
                            (like, like, f"%{directory_filter}%", limit),
                        )
                    else:
                        cursor.execute(
                            """
                            SELECT id, file_path, file_name, resource_name,
                                   directory, size, modified_time
                            FROM files
                            WHERE file_name LIKE ? OR file_path LIKE ?
                            LIMIT ?
                            """,
                            (like, like, limit),
                        )
                    for row in cursor.fetchall():
                        results.append(
                            {
                                "id": row["id"],
                                "file_path": row["file_path"],
                                "file_name": row["file_name"],
                                "resource_name": row["resource_name"],
                                "directory": row["directory"],
                                "size": row["size"],
                                "modified_time": row["modified_time"],
                            }
                        )

                return results
            finally:
                conn.close()

    def search_semantic(
        self,
        query: str,
        limit: int = 10,
        directory_filter: Optional[str] = None,
        max_chunks_per_file: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid semantic search: Use FTS5 to find candidate files, then FAISS to find relevant chunks.

        Args:
            query: Search query
            limit: Maximum number of chunks to return
            directory_filter: Optional directory path to filter results
            max_chunks_per_file: Maximum chunks to return per file

        Returns:
            List of dictionaries with chunk information:
            - 'file_path': Path to the file
            - 'file_name': Name of the file
            - 'resource_name': Resource name
            - 'chunk_index': Index of the chunk
            - 'content': Chunk content
            - 'start_pos': Start position in file
            - 'end_pos': End position in file
            - 'score': Relevance score (distance)
        """
        if not self.enable_semantic_search or not self.vector_index:
            # Fallback to keyword search
            return self.search(query, limit=limit, directory_filter=directory_filter)

        # Step 1: Use FTS5 to find candidate files
        candidate_files = self.search(
            query, limit=50, directory_filter=directory_filter
        )  # Get more candidates

        # If no candidate files found, search all files (semantic search can find relevant content)
        if not candidate_files:
            # Get all files instead of returning empty
            candidate_files = self.get_all_files(directory_filter=directory_filter)
            if not candidate_files:
                return []

        # Step 2: Generate query embedding
        try:
            from .embeddings import get_embedding
            from ..defaults import DEFAULT_CONFIG

            config = DEFAULT_CONFIG.copy()
            embedding_model = config.get("embedding_model", "all-MiniLM-L6-v2")
            query_embedding = get_embedding(query, model_name=embedding_model)
        except Exception as e:
            # If embedding fails, fallback to keyword search
            print(f"Warning: Could not generate query embedding: {e}")
            return self.search(query, limit=limit, directory_filter=directory_filter)

        # Step 3: Search FAISS for relevant chunks in candidate files
        file_paths = [f["file_path"] for f in candidate_files]
        chunk_results = self.vector_index.search(
            query_embedding, k=limit * 2, file_filter=file_paths
        )

        # Step 4: Format results
        results = []
        seen_files = {}  # Track chunks per file

        for chunk_id, distance, metadata in chunk_results:
            file_path = metadata["file_path"]

            # Limit chunks per file
            if file_path not in seen_files:
                seen_files[file_path] = 0
            if seen_files[file_path] >= max_chunks_per_file:
                continue
            seen_files[file_path] += 1

            # Find file metadata
            file_meta = next(
                (f for f in candidate_files if f["file_path"] == file_path), None
            )
            if not file_meta:
                continue

            results.append(
                {
                    "file_path": file_path,
                    "file_name": file_meta.get("file_name", ""),
                    "resource_name": file_meta.get("resource_name", ""),
                    "directory": file_meta.get("directory", ""),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "content": metadata.get("content", ""),
                    "start_pos": metadata.get("start_pos", 0),
                    "end_pos": metadata.get("end_pos", 0),
                    "score": distance,
                }
            )

            if len(results) >= limit:
                break

        return results

    def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information by absolute path."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, file_path, file_name, resource_name,
                           directory, size, modified_time
                    FROM files
                    WHERE file_path = ?
                """,
                    (file_path,),
                )

                row = cursor.fetchone()
                if row:
                    return {
                        "id": row["id"],
                        "file_path": row["file_path"],
                        "file_name": row["file_name"],
                        "resource_name": row["resource_name"],
                        "directory": row["directory"],
                        "size": row["size"],
                        "modified_time": row["modified_time"],
                    }
                return None
            finally:
                conn.close()

    def get_all_files(
        self, directory_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all indexed files, optionally filtered by directory."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if directory_filter:
                    cursor.execute(
                        """
                        SELECT id, file_path, file_name, resource_name,
                               directory, size, modified_time
                        FROM files
                        WHERE directory LIKE ?
                        ORDER BY file_path
                    """,
                        (f"%{directory_filter}%",),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, file_path, file_name, resource_name,
                               directory, size, modified_time
                        FROM files
                        ORDER BY file_path
                    """
                    )

                results = []
                for row in cursor.fetchall():
                    results.append(
                        {
                            "id": row["id"],
                            "file_path": row["file_path"],
                            "file_name": row["file_name"],
                            "resource_name": row["resource_name"],
                            "directory": row["directory"],
                            "size": row["size"],
                            "modified_time": row["modified_time"],
                        }
                    )

                return results
            finally:
                conn.close()

    def remove_directory(self, directory: Path) -> int:
        """
        Remove all files from index that are in the specified directory.

        Returns:
            Number of files removed
        """
        directory_str = str(directory.absolute())

        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.cursor()

                # Get file paths to remove from vector index
                cursor.execute(
                    """
                    SELECT file_path FROM files
                    WHERE file_path LIKE ?
                """,
                    (f"{directory_str}%",),
                )
                file_paths = [row[0] for row in cursor.fetchall()]

                # Delete files in this directory
                cursor.execute(
                    """
                    DELETE FROM files
                    WHERE file_path LIKE ?
                """,
                    (f"{directory_str}%",),
                )

                removed = cursor.rowcount
                conn.commit()

                # Remove from vector index
                if self.enable_semantic_search and self.vector_index:
                    for file_path in file_paths:
                        try:
                            self.vector_index.remove_file(file_path)
                        except Exception:
                            pass
                    self.vector_index.save()

                return removed
            finally:
                conn.close()

    def clear_index(self):
        """Clear all indexed files."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM files")
                cursor.execute("DELETE FROM files_fts")
                conn.commit()
            finally:
                conn.close()

            # Clear vector index
            if self.enable_semantic_search and self.vector_index:
                try:
                    # Reinitialize vector index
                    self.vector_index._init_index()
                    self.vector_index.save()
                except Exception:
                    pass

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM files")
                total_files = cursor.fetchone()[0]

                cursor.execute("SELECT SUM(size) FROM files")
                total_size = cursor.fetchone()[0] or 0

                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT directory) FROM files
                """
                )
                total_directories = cursor.fetchone()[0]

                stats = {
                    "total_files": total_files,
                    "total_size": total_size,
                    "total_directories": total_directories,
                    "database_path": str(self.db_path),
                    "semantic_search_enabled": self.enable_semantic_search,
                }

                # Add vector index stats if available
                if self.enable_semantic_search and self.vector_index:
                    try:
                        vector_stats = self.vector_index.get_stats()
                        stats.update(vector_stats)
                    except Exception:
                        pass

                return stats
            finally:
                conn.close()
