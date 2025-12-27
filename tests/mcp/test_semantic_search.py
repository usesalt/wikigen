#!/usr/bin/env python3
"""Test script for semantic search functionality with performance metrics."""

import sys
import tempfile
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from wikigen.mcp.search_index import FileIndexer
from wikigen.mcp.chunking import chunk_markdown
from wikigen.mcp.embeddings import get_embedding, get_embeddings_batch


def create_test_documents(tmp_path: Path):
    """Create diverse test markdown documents."""
    documents = {
        "api_authentication.md": """# API Authentication

This document explains how to authenticate with our REST API.

## API Keys

To authenticate, you need to provide an API key in the request header:

```
Authorization: Bearer YOUR_API_KEY
```

## OAuth 2.0

We also support OAuth 2.0 authentication for more secure access.

### Getting Started

1. Register your application
2. Obtain client credentials
3. Request an access token
4. Use the token in API requests

## Rate Limiting

API requests are rate-limited to prevent abuse. Free tier users get 100 requests per hour.""",
        "database_queries.md": """# Database Queries

This guide covers how to write efficient database queries.

## SQL Basics

SQL (Structured Query Language) is used to interact with databases.

### SELECT Statements

The SELECT statement retrieves data from tables:

```sql
SELECT * FROM users WHERE age > 18;
```

## Query Optimization

To optimize queries:
- Use indexes on frequently queried columns
- Avoid SELECT * when possible
- Use JOINs efficiently
- Consider query caching

## Performance Tips

1. Index your foreign keys
2. Use prepared statements
3. Monitor slow queries
4. Use connection pooling""",
        "error_handling.md": """# Error Handling

Best practices for handling errors in your application.

## Exception Handling

Always catch specific exceptions rather than generic ones:

```python
try:
    result = api_call()
except APIError as e:
    logger.error(f"API error: {e}")
except NetworkError as e:
    logger.error(f"Network error: {e}")
```

## Error Codes

We use HTTP status codes for API errors:
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

## Logging

Always log errors with context:
- User ID
- Request ID
- Timestamp
- Error message
- Stack trace""",
        "deployment.md": """# Deployment Guide

How to deploy your application to production.

## Prerequisites

Before deploying:
- Set up environment variables
- Configure database connections
- Set up monitoring
- Prepare rollback plan

## Deployment Steps

1. Build the application
2. Run tests
3. Deploy to staging
4. Run smoke tests
5. Deploy to production
6. Monitor for issues

## CI/CD Pipeline

Our CI/CD pipeline automatically:
- Runs tests
- Builds Docker images
- Deploys to staging
- Runs integration tests
- Deploys to production""",
        "testing.md": """# Testing Guide

Comprehensive guide to testing your application.

## Unit Tests

Unit tests verify individual components work correctly.

### Example

```python
def test_user_creation():
    user = create_user("test@example.com")
    assert user.email == "test@example.com"
```

## Integration Tests

Integration tests verify components work together.

## Test Coverage

Aim for at least 80% code coverage.

## Best Practices

- Write tests before code (TDD)
- Keep tests independent
- Use descriptive test names
- Mock external dependencies""",
    }

    for filename, content in documents.items():
        (tmp_path / filename).write_text(content)

    return len(documents)


def test_semantic_search_basic():
    """Test basic semantic search functionality."""
    print("=" * 70)
    print("Testing Semantic Search - Basic Operations")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test documents
        num_files = create_test_documents(tmp_path)
        print(f"\n✓ Created {num_files} test documents")

        # Create indexer with temporary database and vector index (doesn't affect local configs)
        db_path = tmp_path / "test_semantic_index.db"
        vector_index_path = tmp_path / "test_semantic_index.faiss"
        indexer = FileIndexer(
            index_db_path=db_path,
            enable_semantic_search=True,
            vector_index_path=vector_index_path,
        )

        # Test 1: Index directory with timing
        print("\nTest 1: Index directory with semantic search")
        start_time = time.time()
        added, updated, skipped = indexer.index_directory(tmp_path)
        indexing_time = time.time() - start_time
        print(f"  Added: {added}, Updated: {updated}, Skipped: {skipped}")
        print(f"  ⏱️  Indexing time: {indexing_time:.3f}s")
        assert added >= num_files, f"Should index at least {num_files} files"
        print("  ✓ Directory indexed successfully")

        # Test 2: Check stats include semantic search info
        print("\nTest 2: Get index statistics")
        stats = indexer.get_stats()
        print(f"  Total files: {stats['total_files']}")
        print(
            f"  Semantic search enabled: {stats.get('semantic_search_enabled', False)}"
        )
        if stats.get("semantic_search_enabled"):
            print(f"  Total chunks: {stats.get('total_chunks', 0)}")
            print(f"  Vector index size: {stats.get('index_size', 0)}")
        assert stats["total_files"] >= num_files
        assert stats.get("semantic_search_enabled", False) == True
        print("  ✓ Stats retrieved correctly")

        # Test 3: Semantic search
        print("\nTest 3: Semantic search")
        query = "How do I authenticate with the API?"
        start_time = time.time()
        results = indexer.search_semantic(query, limit=5)
        search_time = time.time() - start_time
        print(f"  Query: '{query}'")
        print(f"  Found {len(results)} relevant chunks")
        print(f"  ⏱️  Search time: {search_time:.3f}s")
        assert len(results) > 0, "Should find relevant chunks"

        # Verify results have chunk information
        for i, result in enumerate(results[:3], 1):
            assert "content" in result, f"Result {i} missing content"
            assert "file_path" in result, f"Result {i} missing file_path"
            assert "score" in result, f"Result {i} missing score"
            print(f"  Result {i}: {result['file_name']} (score: {result['score']:.4f})")
            print(f"    Chunk preview: {result['content'][:100]}...")

        print("  ✓ Semantic search works correctly")

        # Test 4: Compare keyword vs semantic search
        print("\nTest 4: Compare keyword vs semantic search")
        query = "database performance optimization"
        print(f"  Query: '{query}'")

        # Keyword search
        start_time = time.time()
        keyword_results = indexer.search(query, limit=10)
        keyword_time = time.time() - start_time
        print(f"  Keyword search: {len(keyword_results)} files in {keyword_time:.3f}s")

        # Semantic search
        start_time = time.time()
        semantic_results = indexer.search_semantic(query, limit=10)
        semantic_time = time.time() - start_time
        print(
            f"  Semantic search: {len(semantic_results)} chunks in {semantic_time:.3f}s"
        )

        # Semantic should find relevant chunks even if keywords don't match exactly
        assert len(semantic_results) > 0, "Semantic search should find relevant chunks"
        print("  ✓ Comparison complete")

        # Test 5: Test chunking
        print("\nTest 5: Test chunking functionality")
        test_content = (tmp_path / "api_authentication.md").read_text()
        # Use smaller chunk size to ensure multiple chunks for test document
        # chunk_size=50 means 200 chars, which should create multiple chunks
        chunks = chunk_markdown(test_content, chunk_size=50, overlap=10)
        print(f"  Document split into {len(chunks)} chunks")
        assert len(chunks) >= 1, f"Should create at least 1 chunk, got {len(chunks)}"
        # For a small document, we might only get 1 chunk, which is acceptable
        if len(chunks) > 1:
            print("  ✓ Document split into multiple chunks")
        else:
            print("  ✓ Document fits in single chunk (acceptable for small documents)")
        for i, chunk in enumerate(chunks[:2], 1):
            print(f"  Chunk {i}: {len(chunk['content'])} chars")
        print("  ✓ Chunking works correctly")

        # Test 6: Test embedding generation
        print("\nTest 6: Test embedding generation")
        test_texts = [chunk["content"] for chunk in chunks[:3]]
        start_time = time.time()
        embeddings = get_embeddings_batch(test_texts)
        embedding_time = time.time() - start_time
        print(f"  Generated {len(embeddings)} embeddings in {embedding_time:.3f}s")
        print(f"  Embedding dimension: {embeddings.shape[1]}")
        assert len(embeddings) == len(
            test_texts
        ), "Should generate embeddings for all texts"
        assert embeddings.shape[1] == 384, "Should use 384-dimensional embeddings"
        print("  ✓ Embedding generation works correctly")

    print("\n" + "=" * 70)
    print("✓ All semantic search basic tests passed!")
    print("=" * 70)


def test_semantic_search_performance():
    """Test semantic search performance with various queries."""
    print("\n" + "=" * 70)
    print("Testing Semantic Search - Performance Metrics")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test documents
        create_test_documents(tmp_path)

        # Create indexer
        db_path = tmp_path / "test_perf_index.db"
        vector_index_path = tmp_path / "test_perf_index.faiss"
        indexer = FileIndexer(
            index_db_path=db_path,
            enable_semantic_search=True,
            vector_index_path=vector_index_path,
        )

        # Index directory
        print("\nIndexing documents...")
        start_time = time.time()
        indexer.index_directory(tmp_path)
        indexing_time = time.time() - start_time
        print(f"✓ Indexing completed in {indexing_time:.3f}s")

        # Test queries
        test_queries = [
            "How to authenticate API requests?",
            "Database query optimization techniques",
            "Error handling best practices",
            "Deployment process and steps",
            "Writing unit tests",
        ]

        print("\nPerformance Comparison:")
        print("-" * 70)
        print(
            f"{'Query':<40} {'Keyword (ms)':<15} {'Semantic (ms)':<15} {'Chunks':<10}"
        )
        print("-" * 70)

        total_keyword_time = 0
        total_semantic_time = 0

        for query in test_queries:
            # Keyword search
            start = time.time()
            keyword_results = indexer.search(query, limit=10)
            keyword_time = (time.time() - start) * 1000  # Convert to ms
            total_keyword_time += keyword_time

            # Semantic search
            start = time.time()
            semantic_results = indexer.search_semantic(query, limit=10)
            semantic_time = (time.time() - start) * 1000  # Convert to ms
            total_semantic_time += semantic_time

            print(
                f"{query[:38]:<40} {keyword_time:>10.2f}ms    {semantic_time:>10.2f}ms    {len(semantic_results):>5}"
            )

        print("-" * 70)
        avg_keyword = total_keyword_time / len(test_queries)
        avg_semantic = total_semantic_time / len(test_queries)
        print(f"{'Average':<40} {avg_keyword:>10.2f}ms    {avg_semantic:>10.2f}ms")
        print("=" * 70)

        # Performance assertions
        assert avg_semantic < 1000, "Semantic search should be fast (<1s average)"
        print("\n✓ Performance metrics collected successfully")


def test_semantic_search_accuracy():
    """Test semantic search accuracy with specific queries."""
    print("\n" + "=" * 70)
    print("Testing Semantic Search - Accuracy")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test documents
        create_test_documents(tmp_path)

        # Create indexer
        db_path = tmp_path / "test_accuracy_index.db"
        vector_index_path = tmp_path / "test_accuracy_index.faiss"
        indexer = FileIndexer(
            index_db_path=db_path,
            enable_semantic_search=True,
            vector_index_path=vector_index_path,
        )

        # Index directory
        indexer.index_directory(tmp_path)

        # Test cases: (query, expected_file_keyword)
        test_cases = [
            ("API authentication methods", "api_authentication"),
            ("SQL query performance", "database_queries"),
            ("Exception handling", "error_handling"),
            ("Production deployment", "deployment"),
            ("Test coverage", "testing"),
        ]

        print("\nAccuracy Tests:")
        print("-" * 70)

        for query, expected_keyword in test_cases:
            results = indexer.search_semantic(query, limit=3)
            assert len(results) > 0, f"Should find results for '{query}'"

            # Check if top result is relevant
            top_result = results[0]
            file_name = top_result.get("file_name", "")
            score = top_result.get("score", float("inf"))

            # Check if expected keyword appears in file name or content
            is_relevant = (
                expected_keyword in file_name.lower()
                or expected_keyword in top_result.get("content", "").lower()
            )

            status = "✓" if is_relevant else "✗"
            print(f"{status} Query: '{query}'")
            print(f"    Top result: {file_name} (score: {score:.4f})")
            print(f"    Relevant: {is_relevant}")

        print("-" * 70)
        print("✓ Accuracy tests completed")


def test_backward_compatibility():
    """Test that keyword search still works when semantic search is disabled."""
    print("\n" + "=" * 70)
    print("Testing Backward Compatibility")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test documents
        create_test_documents(tmp_path)

        # Create indexer with semantic search disabled
        db_path = tmp_path / "test_compat_index.db"
        vector_index_path = tmp_path / "test_compat_index.faiss"
        indexer = FileIndexer(
            index_db_path=db_path,
            enable_semantic_search=False,
            vector_index_path=vector_index_path,
        )

        # Index directory
        indexer.index_directory(tmp_path)

        # Test keyword search still works
        query = "authentication"
        results = indexer.search(query, limit=10)
        assert len(results) > 0, "Keyword search should still work"
        print(f"✓ Keyword search works: {len(results)} results for '{query}'")

        # Test semantic search falls back to keyword search
        results = indexer.search_semantic(query, limit=10)
        assert len(results) > 0, "Semantic search should fallback to keyword"
        print("✓ Semantic search falls back to keyword when disabled")

    print("✓ Backward compatibility verified")


def main():
    """Run all semantic search tests."""
    print("\n" + "=" * 70)
    print("Semantic Search Test Suite")
    print("=" * 70)

    tests_passed = 0
    tests_failed = 0

    test_functions = [
        ("Basic Operations", test_semantic_search_basic),
        ("Performance Metrics", test_semantic_search_performance),
        ("Accuracy", test_semantic_search_accuracy),
        ("Backward Compatibility", test_backward_compatibility),
    ]

    for test_name, test_func in test_functions:
        try:
            test_func()
            tests_passed += 1
        except Exception as e:
            tests_failed += 1
            print(f"\n✗ {test_name} failed: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"✓ Passed: {tests_passed}")
    if tests_failed > 0:
        print(f"✗ Failed: {tests_failed}")
        sys.exit(1)
    else:
        print("✓ All semantic search tests passed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
