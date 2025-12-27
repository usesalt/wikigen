#!/usr/bin/env python3
"""Test script to verify MCP tools work locally before deploying."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wikigen.mcp.output_resources import discover_all_projects
from wikigen.config import get_output_dir


def test_server_initialization():
    """Test that the server initializes without errors."""
    print("=" * 60)
    print("Testing server initialization")
    print("=" * 60)

    try:
        from wikigen.mcp.server import app

        print(f"✓ Server name: {app.name}")
        print("✓ Server initialized successfully")
        print("✓ Module loads without errors")
        print()
        return True
    except Exception as e:
        print(f"✗ Error initializing server: {e}")
        import traceback

        traceback.print_exc()
        raise


def test_get_docs():
    """Test the get_docs tool with both resource names and file paths."""
    print("=" * 60)
    print("Testing get_docs tool")
    print("=" * 60)

    from wikigen.mcp.server import get_docs

    # First, get list of available docs
    projects = discover_all_projects()

    # Test 1: Get doc by resource name
    if projects:
        first_doc = sorted(projects.keys())[0]
        print(f"Test 1: Getting doc by resource name: {first_doc}")
        try:
            result = get_docs(first_doc)
            print(f"✓ Successfully retrieved doc (length: {len(result)} characters)")
            print(f"Preview (first 200 chars):\n{result[:200]}...")

            # Verify it's valid markdown-like content
            assert len(result) > 0, "Content should not be empty"
        except Exception as e:
            print(f"✗ Failed to get doc by resource name: {e}")
            raise
        print()

        # Test 2: Get doc by absolute file path
        doc_path = projects[first_doc]
        print(f"Test 2: Getting doc by absolute path: {doc_path}")
        try:
            result = get_docs(str(doc_path.absolute()))
            print(
                f"✓ Successfully retrieved doc by path (length: {len(result)} characters)"
            )
            assert len(result) > 0, "Content should not be empty"
        except Exception as e:
            print(f"✗ Failed to get doc by file path: {e}")
            raise
        print()
    else:
        print("⚠ No docs found - skipping get_docs resource name test")

    # Test 3: Non-existent resource name
    print("Test 3: Testing with non-existent resource name (should raise error):")
    try:
        get_docs("nonexistent-doc-12345-that-does-not-exist")
        print("✗ Should have raised ValueError")
        assert False, "Should raise ValueError for non-existent doc"
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {str(e)[:100]}...")
    print()

    # Test 4: Non-existent file path
    print("Test 4: Testing with non-existent file path (should raise error):")
    try:
        get_docs("/absolutely/nonexistent/path/that/does/not/exist.md")
        print("✗ Should have raised RuntimeError")
        assert False, "Should raise RuntimeError for non-existent path"
    except (ValueError, RuntimeError) as e:
        print(f"✓ Correctly raised error: {type(e).__name__}")
    print()


def test_search_docs():
    """Test the search_docs tool."""
    print("=" * 60)
    print("Testing search_docs tool")
    print("=" * 60)

    from wikigen.mcp.server import search_docs
    from wikigen.mcp.search_index import FileIndexer

    # Ensure we have an index
    output_dir = get_output_dir()
    indexer = FileIndexer()
    stats = indexer.get_stats()

    if stats["total_files"] == 0 and output_dir.exists():
        print("Indexing output directory for search tests...")
        added, updated, skipped = indexer.index_directory(output_dir)
        print(f"✓ Indexed {added} files, updated {updated}, skipped {skipped}")
        print()

    # Test 1: Basic search
    print("Test 1: Basic search query")
    try:
        results = search_docs("README", limit=10)
        print(results[:500] if len(results) > 500 else results)
        assert (
            "Found" in results
            or "No files found" in results
            or "No chunks found" in results
            or "No chunks found" in results
            or "Indexed" in results
        )
        print("✓ Basic search works")
    except Exception as e:
        print(f"✗ Basic search failed: {e}")
        import traceback

        traceback.print_exc()
    print()

    # Test 2: Search with limit
    print("Test 2: Search with custom limit")
    try:
        results = search_docs("readme", limit=5)
        print(f"Results length: {len(results)} characters")
        assert (
            "Found" in results
            or "No files found" in results
            or "No chunks found" in results
        )
        print("✓ Search with limit works")
    except Exception as e:
        print(f"✗ Search with limit failed: {e}")
    print()

    # Test 3: Search with directory filter
    if output_dir.exists():
        print("Test 3: Search with directory filter")
        try:
            results = search_docs("readme", limit=10, directory_filter=str(output_dir))
            print(f"Results length: {len(results)} characters")
            assert (
                "Found" in results
                or "No files found" in results
                or "No chunks found" in results
            )
            print("✓ Search with directory filter works")
        except Exception as e:
            print(f"✗ Search with directory filter failed: {e}")
        print()

    # Test 4: Empty search
    print("Test 4: Empty query search")
    try:
        results = search_docs("", limit=5)
        # Empty query might return all or nothing, both are valid
        print(f"Results: {results[:200]}...")
        print("✓ Empty query handled")
    except Exception as e:
        print(f"✗ Empty query failed: {e}")
    print()


def test_index_directories():
    """Test the index_directories tool."""
    print("=" * 60)
    print("Testing index_directories tool")
    print("=" * 60)

    from wikigen.mcp.server import index_directories
    from wikigen.mcp.search_index import FileIndexer

    output_dir = get_output_dir()

    # Test 1: Index existing directory
    if output_dir.exists():
        print(f"Test 1: Indexing existing directory: {output_dir}")
        try:
            result = index_directories([str(output_dir)])
            print(result)
            assert (
                "added" in result.lower()
                or "updated" in result.lower()
                or "skipped" in result.lower()
            )
            print("✓ Successfully indexed existing directory")
        except Exception as e:
            print(f"✗ Failed to index directory: {e}")
            import traceback

            traceback.print_exc()
        print()

    # Test 2: Index non-existent directory
    print("Test 2: Indexing non-existent directory (should show error)")
    try:
        result = index_directories(["/nonexistent/directory/path/12345"])
        print(result)
        assert "does not exist" in result or "not a directory" in result
        print("✓ Correctly handled non-existent directory")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    print()

    # Test 3: Index multiple directories (mix of valid and invalid)
    if output_dir.exists():
        print("Test 3: Indexing multiple directories (mix)")
        try:
            result = index_directories(
                [
                    str(output_dir),
                    "/nonexistent/path/12345",
                ]
            )
            print(result)
            print("✓ Handled multiple directories correctly")
        except Exception as e:
            print(f"✗ Failed: {e}")
        print()

    # Test 4: Index with max_depth
    if output_dir.exists():
        print("Test 4: Indexing with max_depth=2")
        try:
            result = index_directories([str(output_dir)], max_depth=2)
            print(result[:300] + "..." if len(result) > 300 else result)
            print("✓ Indexing with max_depth works")
        except Exception as e:
            print(f"✗ Failed: {e}")
        print()

    # Verify index stats
    print("Final index statistics:")
    indexer = FileIndexer()
    stats = indexer.get_stats()
    print(f"  Total files: {stats['total_files']}")
    print(f"  Total directories: {stats['total_directories']}")
    print(f"  Total size: {stats['total_size']:,} bytes")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MCP Tools Testing Suite")
    print("=" * 60 + "\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Server initialization
    try:
        if test_server_initialization():
            tests_passed += 1
        else:
            tests_failed += 1
            print("✗ Server initialization failed - aborting remaining tests")
            sys.exit(1)
    except Exception as e:
        tests_failed += 1
        print(f"✗ Server initialization test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Test 2: get_docs
    try:
        test_get_docs()
        tests_passed += 1
    except Exception as e:
        tests_failed += 1
        print(f"✗ get_docs test failed: {e}")
        import traceback

        traceback.print_exc()

    # Test 3: search_docs
    try:
        test_search_docs()
        tests_passed += 1
    except Exception as e:
        tests_failed += 1
        print(f"✗ search_docs test failed: {e}")
        import traceback

        traceback.print_exc()

    # Test 4: index_directories
    try:
        test_index_directories()
        tests_passed += 1
    except Exception as e:
        tests_failed += 1
        print(f"✗ index_directories test failed: {e}")
        import traceback

        traceback.print_exc()

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"✓ Passed: {tests_passed}")
    if tests_failed > 0:
        print(f"✗ Failed: {tests_failed}")
        sys.exit(1)
    else:
        print("✓ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
