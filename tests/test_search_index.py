#!/usr/bin/env python3
"""Test script for search_index functionality."""

import sys
import tempfile
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from salt_docs.mcp.search_index import FileIndexer


def test_file_indexer_basic():
    """Test basic file indexing functionality."""
    print("=" * 60)
    print("Testing SearchIndex - Basic Operations")
    print("=" * 60)

    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test markdown files
        (tmp_path / "test1.md").write_text("# Test 1\nContent here")
        (tmp_path / "test2.md").write_text("# Test 2\nMore content")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "test3.md").write_text("# Test 3\nNested content")

        # Create indexer with temporary database
        db_path = tmp_path / "test_index.db"
        indexer = FileIndexer(index_db_path=db_path)

        # Test 1: Index directory
        print("\nTest 1: Index directory")
        added, updated, skipped = indexer.index_directory(tmp_path)
        print(f"  Added: {added}, Updated: {updated}, Skipped: {skipped}")
        assert added >= 3, f"Should index at least 3 files, got {added}"
        print("  ✓ Directory indexed successfully")

        # Test 2: Get stats
        print("\nTest 2: Get index statistics")
        stats = indexer.get_stats()
        print(f"  Total files: {stats['total_files']}")
        print(f"  Total directories: {stats['total_directories']}")
        assert stats["total_files"] >= 3
        print("  ✓ Stats retrieved correctly")

        # Test 3: Search
        print("\nTest 3: Search indexed files")
        results = indexer.search("test", limit=10)
        print(f"  Found {len(results)} results")
        assert len(results) >= 3, "Should find at least 3 test files"

        for result in results:
            assert "file_path" in result
            assert "resource_name" in result
            assert "file_name" in result
        print("  ✓ Search works correctly")

        # Test 4: Get all files
        print("\nTest 4: Get all indexed files")
        all_files = indexer.get_all_files()
        print(f"  Total files: {len(all_files)}")
        assert len(all_files) >= 3
        print("  ✓ Get all files works")

        # Test 5: Get file by path
        print("\nTest 5: Get file by path")
        test_file = tmp_path / "test1.md"
        file_info = indexer.get_file_by_path(str(test_file.absolute()))
        assert file_info is not None
        assert file_info["file_name"] == "test1.md"
        print("  ✓ Get file by path works")

        # Test 6: Update detection (modify file and re-index)
        print("\nTest 6: Update detection")
        (tmp_path / "test1.md").write_text("# Test 1 Updated\nNew content")
        added2, updated2, skipped2 = indexer.index_directory(tmp_path)
        assert updated2 >= 1, "Should detect at least one updated file"
        print(f"  Updated: {updated2} files detected")
        print("  ✓ Update detection works")

        # Test 7: Remove directory
        print("\nTest 7: Remove directory from index")
        removed = indexer.remove_directory(tmp_path)
        assert removed >= 3, f"Should remove at least 3 files, got {removed}"
        print(f"  Removed {removed} files")

        stats_after = indexer.get_stats()
        assert stats_after["total_files"] < stats["total_files"]
        print("  ✓ Directory removal works")

        # Test 8: Clear index
        print("\nTest 8: Clear index")
        # Re-index first
        indexer.index_directory(tmp_path)
        indexer.clear_index()
        stats_cleared = indexer.get_stats()
        assert stats_cleared["total_files"] == 0
        print("  ✓ Clear index works")

    print("\n" + "=" * 60)
    print("✓ All SearchIndex basic tests passed!")
    print("=" * 60)


def test_file_indexer_search():
    """Test search functionality with various queries."""
    print("\n" + "=" * 60)
    print("Testing SearchIndex - Search Functionality")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create diverse test files
        (tmp_path / "README.md").write_text("# Project Readme\nMain documentation")
        (tmp_path / "api.md").write_text("# API Documentation\nREST API endpoints")
        (tmp_path / "guide.md").write_text("# User Guide\nHow to use the system")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "advanced.md").write_text(
            "# Advanced Topics\nComplex features"
        )

        db_path = tmp_path / "search_test.db"
        indexer = FileIndexer(index_db_path=db_path)
        indexer.index_directory(tmp_path)

        # Test 1: Single word search
        print("\nTest 1: Single word search")
        results = indexer.search("README", limit=10)
        assert len(results) >= 1
        assert any("README" in r["file_name"] for r in results)
        print("  ✓ Single word search works")

        # Test 2: Multi-word search
        print("\nTest 2: Multi-word search")
        results = indexer.search("API Documentation", limit=10)
        assert len(results) >= 1
        print("  ✓ Multi-word search works")

        # Test 3: Search with directory filter
        print("\nTest 3: Search with directory filter")
        results = indexer.search(
            "advanced", limit=10, directory_filter=str(tmp_path / "docs")
        )
        assert len(results) >= 1
        print("  ✓ Directory filter works")

        # Test 4: Empty results
        print("\nTest 4: Search with no results")
        results = indexer.search("nonexistentkeyword12345", limit=10)
        assert len(results) == 0
        print("  ✓ Empty results handled correctly")

    print("\n" + "=" * 60)
    print("✓ All search tests passed!")
    print("=" * 60)


def main():
    """Run all file_indexer tests."""
    print("\n" + "=" * 60)
    print("SearchIndex Test Suite")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    try:
        test_file_indexer_basic()
        tests_passed += 1
    except Exception as e:
        tests_failed += 1
        print(f"\n✗ Basic tests failed: {e}")
        import traceback

        traceback.print_exc()

    try:
        test_file_indexer_search()
        tests_passed += 1
    except Exception as e:
        tests_failed += 1
        print(f"\n✗ Search tests failed: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"✓ Passed: {tests_passed}")
    if tests_failed > 0:
        print(f"✗ Failed: {tests_failed}")
        sys.exit(1)
    else:
        print("✓ All SearchIndex tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
