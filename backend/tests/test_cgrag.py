#!/usr/bin/env python3
"""Test script to verify CGRAG retrieval."""

import asyncio
from pathlib import Path
from app.services.cgrag import CGRAGIndexer, CGRAGRetriever

async def main():
    # Load index
    project_root = Path(__file__).parent.parent
    index_path = project_root / "data" / "faiss_indexes" / "docs.index"
    metadata_path = project_root / "data" / "faiss_indexes" / "docs_metadata.pkl"

    print(f"Loading index from: {index_path}")
    print(f"Loading metadata from: {metadata_path}")
    print(f"Index exists: {index_path.exists()}")
    print(f"Metadata exists: {metadata_path.exists()}")

    if not index_path.exists() or not metadata_path.exists():
        print("ERROR: Index files not found!")
        return

    # Load indexer
    indexer = CGRAGIndexer.load_index(index_path, metadata_path)
    print(f"Loaded indexer with {len(indexer.chunks)} chunks")

    # Create retriever
    retriever = CGRAGRetriever(indexer=indexer, min_relevance=0.0)
    print("Created retriever (min_relevance=0.0 for debugging)")

    # Test query
    query = "What was delivered in Session 1?"
    print(f"\nQuery: {query}")

    # Manually test to see raw distances
    import faiss
    query_embedding = indexer.encoder.encode([query], show_progress_bar=False, convert_to_numpy=True)
    query_embedding = query_embedding[0].reshape(1, -1)
    faiss.normalize_L2(query_embedding)

    distances, indices = indexer.index.search(query_embedding, 5)
    print(f"\nRaw FAISS distances (L2): {distances[0]}")
    print(f"FAISS distances squared (L2^2): {distances[0] ** 2}")
    print(f"Converted scores (1 - L2^2/2): {1.0 - ((distances[0] ** 2) / 2.0)}")

    result = await retriever.retrieve(
        query=query,
        token_budget=8000,
        max_artifacts=10
    )

    print("\nRetrieval Results:")
    print(f"  Artifacts: {len(result.artifacts)}")
    print(f"  Tokens used: {result.tokens_used}")
    print(f"  Retrieval time: {result.retrieval_time_ms:.2f}ms")
    print(f"  Candidates considered: {result.candidates_considered}")
    print(f"  Top scores: {result.top_scores[:5]}")

    # Print top artifacts
    print("\nTop Artifacts:")
    for i, artifact in enumerate(result.artifacts[:3]):
        print(f"\n  Artifact {i+1}:")
        print(f"    File: {artifact.file_path}")
        print(f"    Relevance: {artifact.relevance_score:.3f}")
        print(f"    Chunk: {artifact.chunk_index}")
        print(f"    Content preview: {artifact.content[:200]}...")

if __name__ == "__main__":
    asyncio.run(main())
