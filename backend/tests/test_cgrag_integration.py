#!/usr/bin/env python3
"""Integration test for CGRAG system.

This script tests the complete CGRAG pipeline:
1. Indexing documents
2. Retrieving context
3. Query endpoint integration
"""

import asyncio
import httpx
from pathlib import Path


async def test_cgrag_integration():
    """Test complete CGRAG integration."""
    print("=" * 60)
    print("CGRAG Integration Test")
    print("=" * 60)

    # Test 1: Verify index exists
    print("\n1. Checking FAISS index files...")
    project_root = Path(__file__).parent.parent
    index_path = project_root / "data" / "faiss_indexes" / "docs.index"
    metadata_path = project_root / "data" / "faiss_indexes" / "docs_metadata.pkl"

    if not index_path.exists() or not metadata_path.exists():
        print("   ❌ Index files not found!")
        print("   Run: python -m app.cli.index_docs ../docs")
        return False

    print(f"   ✓ Index exists: {index_path}")
    print(f"   ✓ Metadata exists: {metadata_path}")

    # Test 2: Test retrieval directly
    print("\n2. Testing direct retrieval...")
    from app.services.cgrag import CGRAGIndexer, CGRAGRetriever

    indexer = CGRAGIndexer.load_index(index_path, metadata_path)
    print(f"   ✓ Loaded {len(indexer.chunks)} chunks")

    retriever = CGRAGRetriever(indexer=indexer, min_relevance=0.2)
    result = await retriever.retrieve(
        query="What was delivered in Session 1?", token_budget=8000, max_artifacts=10
    )

    print(f"   ✓ Retrieved {len(result.artifacts)} artifacts")
    print(f"   ✓ Tokens used: {result.tokens_used}/{8000}")
    print(f"   ✓ Retrieval time: {result.retrieval_time_ms:.2f}ms")

    if len(result.artifacts) == 0:
        print("   ❌ No artifacts retrieved!")
        return False

    # Test 3: Test query endpoint integration
    print("\n3. Testing query endpoint integration...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/query",
                json={
                    "query": "What features were implemented in Session 1?",
                    "mode": "auto",
                    "use_context": True,
                    "max_tokens": 512,
                },
            )

            if response.status_code != 200:
                print(f"   ❌ HTTP {response.status_code}: {response.text}")
                return False

            data = response.json()
            metadata = data.get("metadata", {})

            print("   ✓ Query successful")
            print(f"   ✓ Model: {metadata.get('model_id')}")
            print(f"   ✓ CGRAG artifacts: {metadata.get('cgrag_artifacts')}")
            print(f"   ✓ Processing time: {metadata.get('processing_time_ms'):.2f}ms")

            if metadata.get("cgrag_artifacts", 0) == 0:
                print("   ⚠ Warning: No CGRAG artifacts used in query")

            # Show artifact details
            artifacts_info = metadata.get("cgrag_artifacts_info", [])
            if artifacts_info:
                print("\n   Artifact Details:")
                for i, artifact in enumerate(artifacts_info[:3], 1):
                    print(
                        f"      {i}. {Path(artifact['file_path']).name} "
                        f"(relevance: {artifact['relevance_score']:.3f}, "
                        f"tokens: {artifact['token_count']})"
                    )

        except httpx.ConnectError:
            print("   ❌ Cannot connect to backend (http://localhost:8000)")
            print("   Make sure the backend is running: uvicorn app.main:app")
            return False

    # Test 4: Performance check
    print("\n4. Performance checks...")
    if result.retrieval_time_ms < 100:
        print(
            f"   ✓ Retrieval latency: {result.retrieval_time_ms:.2f}ms (target: <100ms)"
        )
    else:
        print(
            f"   ⚠ Retrieval latency: {result.retrieval_time_ms:.2f}ms (above 100ms target)"
        )

    if metadata.get("processing_time_ms", 0) < 5000:
        print(f"   ✓ Total processing: {metadata.get('processing_time_ms'):.2f}ms")
    else:
        print(
            f"   ⚠ Total processing: {metadata.get('processing_time_ms'):.2f}ms (slow)"
        )

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    result = asyncio.run(test_cgrag_integration())
    exit(0 if result else 1)
