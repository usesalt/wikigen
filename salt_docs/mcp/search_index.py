"""Fast file indexing system using SQLite FTS for machine-wide markdown search.

This module provides indexed search capabilities across multiple directories using
SQLite FTS5 for full-text search of file paths, names, and resource names.
"""

import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from threading import Lock
import hashlib

from ..config import CONFIG_DIR


class FileIndexer:
    """
    Fast file indexer using SQLite FTS5 for efficient full-text search.

    Indexes markdown files across configured directories and provides
    fast search capabilities through SQLite's full-text search engine.
    """

    def __init__(self, index_db_path: Optional[Path] = None):
        """
        Initialize the file indexer.

        Args:
            index_db_path: Path to SQLite database. Defaults to config_dir/file_index.db
        """
        if index_db_path is None:
            index_db_path = CONFIG_DIR / "file_index.db"

        self.db_path = index_db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
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

                    except Exception:
                        # Skip files we can't read or process
                        files_skipped += 1
                        continue

                conn.commit()
            finally:
                conn.close()

        return (files_added, files_updated, files_skipped)

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
                    # Use prefix matching for partial word matches
                    # FTS5 supports prefix matching with token* syntax
                    words = query.strip().split()
                    escaped_words = []
                    for word in words:
                        word = word.strip()
                        if word:
                            # Use prefix matching (*) to match partial tokens
                            # This allows "test" to match "test1", "test2", etc.
                            # Remove any existing * to avoid double wildcards
                            word = word.rstrip("*")
                            escaped_words.append(f"{word}*")
                    fts_query = " OR ".join(escaped_words) if escaped_words else "*"

                # Build SQL query
                if directory_filter:
                    sql = """
                        SELECT f.id, f.file_path, f.file_name, f.resource_name,
                               f.directory, f.size, f.modified_time
                        FROM files_fts
                        JOIN files f ON files_fts.rowid = f.id
                        WHERE files_fts MATCH ? AND f.directory LIKE ?
                        ORDER BY files_fts.rank
                        LIMIT ?
                    """
                    cursor.execute(sql, (fts_query, f"%{directory_filter}%", limit))
                else:
                    sql = """
                        SELECT f.id, f.file_path, f.file_name, f.resource_name,
                               f.directory, f.size, f.modified_time
                        FROM files_fts
                        JOIN files f ON files_fts.rowid = f.id
                        WHERE files_fts MATCH ?
                        ORDER BY files_fts.rank
                        LIMIT ?
                    """
                    cursor.execute(sql, (fts_query, limit))

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

                return {
                    "total_files": total_files,
                    "total_size": total_size,
                    "total_directories": total_directories,
                    "database_path": str(self.db_path),
                }
            finally:
                conn.close()
