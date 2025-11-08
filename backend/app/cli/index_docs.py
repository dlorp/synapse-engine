#!/usr/bin/env python3
"""CLI script to index documentation into FAISS vector database.

This script indexes documents from a specified directory (or docs/ by default)
into a FAISS vector database for CGRAG context retrieval.

Usage:
    python -m app.cli.index_docs [directory]

Example:
    python -m app.cli.index_docs ../docs
    python -m app.cli.index_docs  # Uses ../docs by default
"""

import asyncio
import sys
from pathlib import Path

from app.services.cgrag import CGRAGIndexer, get_cgrag_index_paths
from app.core.config import load_config
from app.services import runtime_settings as settings_service


async def main() -> int:
    """Index documents from specified directory.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Determine directory to index
    if len(sys.argv) > 1:
        docs_dir = Path(sys.argv[1])
    else:
        # Default to docs/ directory relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        docs_dir = project_root / "docs"

    if not docs_dir.exists():
        print(f"Error: Directory {docs_dir} does not exist")
        return 1

    print(f"Indexing documents from: {docs_dir}")

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1

    # Load runtime settings for indexing configuration
    try:
        settings = await settings_service.load_runtime_settings()
        embedding_model = settings.embedding_model_name
        chunk_size = settings.cgrag_chunk_size
        chunk_overlap = settings.cgrag_chunk_overlap
        print("Using runtime settings for indexing")
    except Exception as e:
        # Fallback to config if runtime settings unavailable
        print(f"Warning: Could not load runtime settings ({e}), falling back to config")
        embedding_model = config.cgrag.indexing.embedding_model
        chunk_size = config.cgrag.indexing.chunk_size
        chunk_overlap = config.cgrag.indexing.chunk_overlap

    print(f"Configuration:")
    print(f"  Embedding model: {embedding_model}")
    print(f"  Chunk size: {chunk_size} tokens")
    print(f"  Chunk overlap: {chunk_overlap} tokens")
    print()

    # Create indexer
    try:
        indexer = CGRAGIndexer(embedding_model=embedding_model)
    except Exception as e:
        print(f"Error creating indexer: {e}")
        return 1

    # Index directory
    try:
        num_chunks = await indexer.index_directory(
            directory=docs_dir,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        print(f"\nIndexed {num_chunks} chunks")
    except Exception as e:
        print(f"Error during indexing: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Save index
    try:
        # Get index paths using runtime settings
        index_dir, index_path, metadata_path = get_cgrag_index_paths("docs")

        # Create index directory if it doesn't exist
        index_dir.mkdir(parents=True, exist_ok=True)

        indexer.save_index(index_path, metadata_path)
        print(f"\nSaved index to: {index_path}")
        print(f"Saved metadata to: {metadata_path}")
    except Exception as e:
        print(f"Error saving index: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\nIndexing complete!")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
