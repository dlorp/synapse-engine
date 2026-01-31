"""CGRAG context management for Code Chat mode.

This module provides functions to list, create, refresh, and manage CGRAG indexes
for use in Code Chat mode. Indexes are stored in the backend/data/faiss_indexes/
directory with metadata and chunk information.

Author: CGRAG Specialist
Phase: Code Chat Implementation (Phase 1.1)
"""

import json
import logging
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import faiss
from pydantic import BaseModel, Field

from app.models.code_chat import ContextInfo
from app.services.cgrag import CGRAGIndexer, DocumentChunk
from app.services.event_bus import EventBus

logger = logging.getLogger(__name__)

# Directory where FAISS indexes are stored
FAISS_INDEX_DIR = Path("/app/data/faiss_indexes")

# Supported file extensions for indexing
INDEXABLE_EXTENSIONS = {
    # Code
    ".py", ".pyi",                          # Python
    ".ts", ".tsx", ".js", ".jsx",           # JavaScript/TypeScript
    ".rs",                                  # Rust
    ".go",                                  # Go
    ".java", ".kt",                         # JVM languages
    ".c", ".cpp", ".cc", ".h", ".hpp",      # C/C++
    # Markup/Documentation
    ".md", ".mdx", ".rst",                  # Documentation
    ".txt",                                 # Plain text
    # Configuration
    ".yaml", ".yml", ".toml", ".json",      # Config files
    ".html", ".css", ".scss", ".sass",      # Web
}

# Maximum file size to index (1MB)
MAX_FILE_SIZE = 1024 * 1024


class IndexMetadata(BaseModel):
    """Metadata stored alongside FAISS index.

    Attributes:
        name: Index identifier
        source_path: Source directory that was indexed
        embedding_model: Embedding model used for vectors
        chunk_count: Number of chunks in index
        file_count: Number of files indexed
        created_at: Index creation timestamp
        last_indexed: Last indexing timestamp
        indexed_files: List of indexed file paths
        index_version: Metadata format version
    """
    name: str = Field(..., description="Index identifier")
    source_path: str = Field(..., description="Source directory")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model")
    chunk_count: int = Field(..., ge=0, description="Number of chunks")
    file_count: int = Field(..., ge=0, description="Number of files")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    last_indexed: datetime = Field(default_factory=datetime.now, description="Last indexed timestamp")
    indexed_files: List[str] = Field(default_factory=list, description="Indexed file paths")
    index_version: str = Field(default="1.0", description="Metadata version")


def get_index_path(name: str) -> Path:
    """Get path to FAISS index file.

    Args:
        name: Index name

    Returns:
        Path to .index file
    """
    return FAISS_INDEX_DIR / f"{name}.index"


def get_metadata_path(name: str) -> Path:
    """Get path to metadata JSON file.

    Args:
        name: Index name

    Returns:
        Path to .meta.json file
    """
    return FAISS_INDEX_DIR / f"{name}.meta.json"


def get_chunks_path(name: str) -> Path:
    """Get path to chunks pickle file.

    Args:
        name: Index name

    Returns:
        Path to .chunks.pkl file
    """
    return FAISS_INDEX_DIR / f"{name}.chunks.pkl"


async def list_cgrag_indexes() -> List[ContextInfo]:
    """List all available CGRAG indexes.

    Scans the data/faiss_indexes/ directory for:
    - .index files (FAISS indexes)
    - Associated metadata files (.meta.json)

    Returns:
        List of ContextInfo objects for each index

    Example:
        >>> indexes = await list_cgrag_indexes()
        >>> for idx in indexes:
        ...     print(f"{idx.name}: {idx.chunk_count} chunks")
    """
    logger.info(f"Scanning {FAISS_INDEX_DIR} for CGRAG indexes")

    # Ensure directory exists
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

    indexes = []

    # Find all .index files
    for index_path in FAISS_INDEX_DIR.glob("*.index"):
        name = index_path.stem
        metadata_path = get_metadata_path(name)

        if not metadata_path.exists():
            logger.warning(f"Index {name} has no metadata file, skipping")
            continue

        try:
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata_dict = json.load(f)

            metadata = IndexMetadata(**metadata_dict)

            # Create ContextInfo
            context = ContextInfo(
                name=metadata.name,
                path=str(index_path),
                chunk_count=metadata.chunk_count,
                last_indexed=metadata.last_indexed,
                source_path=metadata.source_path,
                embedding_model=metadata.embedding_model
            )
            indexes.append(context)

        except Exception as e:
            logger.error(f"Failed to load metadata for {name}: {e}")

    logger.info(f"Found {len(indexes)} CGRAG indexes")
    return indexes


async def get_context_info(name: str) -> Optional[ContextInfo]:
    """Get information about a specific CGRAG index.

    Args:
        name: Index name

    Returns:
        ContextInfo if index exists, None otherwise

    Example:
        >>> info = await get_context_info("my_project")
        >>> if info:
        ...     print(f"Index has {info.chunk_count} chunks")
    """
    indexes = await list_cgrag_indexes()
    for idx in indexes:
        if idx.name == name:
            return idx
    return None


async def create_cgrag_index(
    name: str,
    source_path: str,
    embedding_model: str = "all-MiniLM-L6-v2"
) -> ContextInfo:
    """Create a new CGRAG index from a source directory.

    Steps:
    1. Validate source_path exists and is readable
    2. Scan for indexable files
    3. Chunk files using standard chunking strategy (512 words, 50 word overlap)
    4. Generate embeddings using sentence-transformers
    5. Create FAISS index
    6. Save index, chunks, and metadata to data/faiss_indexes/
    7. Return ContextInfo for the new index

    Args:
        name: Index identifier
        source_path: Source directory to index
        embedding_model: Embedding model to use (default: all-MiniLM-L6-v2)

    Returns:
        ContextInfo for the created index

    Raises:
        ValueError: If source_path doesn't exist or name already exists

    Example:
        >>> info = await create_cgrag_index(
        ...     name="my_project",
        ...     source_path="/workspace/my-project"
        ... )
        >>> print(f"Indexed {info.chunk_count} chunks")
    """
    logger.info(f"Creating CGRAG index '{name}' from {source_path}")

    # Validate source path
    source_dir = Path(source_path)
    if not source_dir.exists():
        raise ValueError(f"Source path does not exist: {source_path}")
    if not source_dir.is_dir():
        raise ValueError(f"Source path is not a directory: {source_path}")

    # Check if index already exists
    existing = await get_context_info(name)
    if existing:
        raise ValueError(f"Index '{name}' already exists. Use refresh_cgrag_index() to update.")

    # Ensure index directory exists
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Emit start event
    await EventBus.emit("cgrag_index_start", {
        "name": name,
        "source_path": source_path,
        "status": "starting"
    })

    start_time = time.time()

    try:
        # Collect indexable files
        files = _collect_indexable_files(source_dir)
        logger.info(f"Found {len(files)} indexable files")

        await EventBus.emit("cgrag_index_progress", {
            "name": name,
            "status": "scanning",
            "files_found": len(files)
        })

        # Create indexer and index directory
        indexer = CGRAGIndexer(embedding_model=embedding_model)
        chunk_count = await indexer.index_directory(
            directory=source_dir,
            chunk_size=512,
            chunk_overlap=50,
            batch_size=32
        )

        await EventBus.emit("cgrag_index_progress", {
            "name": name,
            "status": "embedding",
            "chunk_count": chunk_count
        })

        # Save index and chunks
        index_path = get_index_path(name)
        chunks_path = get_chunks_path(name)

        # Save FAISS index
        faiss.write_index(indexer.index, str(index_path))
        logger.info(f"Saved FAISS index to {index_path}")

        # Save chunks
        with open(chunks_path, 'wb') as f:
            pickle.dump([chunk.model_dump() for chunk in indexer.chunks], f)
        logger.info(f"Saved {len(indexer.chunks)} chunks to {chunks_path}")

        # Create metadata
        metadata = IndexMetadata(
            name=name,
            source_path=str(source_dir),
            embedding_model=embedding_model,
            chunk_count=chunk_count,
            file_count=len(files),
            indexed_files=[str(f) for f in files]
        )

        # Save metadata
        metadata_path = get_metadata_path(name)
        with open(metadata_path, 'w') as f:
            json.dump(metadata.model_dump(mode='json'), f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")

        elapsed = time.time() - start_time
        logger.info(
            f"Created index '{name}': {chunk_count} chunks from {len(files)} files "
            f"in {elapsed:.2f}s ({chunk_count/elapsed:.1f} chunks/sec)"
        )

        # Emit completion event
        await EventBus.emit("cgrag_index_complete", {
            "name": name,
            "status": "complete",
            "chunk_count": chunk_count,
            "file_count": len(files),
            "elapsed_seconds": elapsed
        })

        # Return ContextInfo
        return ContextInfo(
            name=name,
            path=str(index_path),
            chunk_count=chunk_count,
            last_indexed=metadata.last_indexed,
            source_path=str(source_dir),
            embedding_model=embedding_model
        )

    except Exception as e:
        logger.error(f"Failed to create index '{name}': {e}")
        await EventBus.emit("cgrag_index_error", {
            "name": name,
            "status": "error",
            "error": str(e)
        })
        raise


async def refresh_cgrag_index(name: str) -> ContextInfo:
    """Re-index an existing CGRAG context.

    Loads the existing index metadata, re-scans the source directory,
    and rebuilds the index with updated content.

    Args:
        name: Index name to refresh

    Returns:
        Updated ContextInfo

    Raises:
        ValueError: If index doesn't exist

    Example:
        >>> info = await refresh_cgrag_index("my_project")
        >>> print(f"Refreshed: {info.chunk_count} chunks")
    """
    logger.info(f"Refreshing CGRAG index '{name}'")

    # Load existing metadata
    metadata_path = get_metadata_path(name)
    if not metadata_path.exists():
        raise ValueError(f"Index '{name}' does not exist")

    with open(metadata_path, 'r') as f:
        metadata_dict = json.load(f)

    metadata = IndexMetadata(**metadata_dict)

    # Delete old files
    await delete_cgrag_index(name)

    # Re-create index with same source path and embedding model
    return await create_cgrag_index(
        name=name,
        source_path=metadata.source_path,
        embedding_model=metadata.embedding_model
    )


async def delete_cgrag_index(name: str) -> bool:
    """Delete a CGRAG index and its metadata.

    Removes:
    - FAISS index file (.index)
    - Chunks file (.chunks.pkl)
    - Metadata file (.meta.json)

    Args:
        name: Index name to delete

    Returns:
        True if deleted, False if didn't exist

    Example:
        >>> deleted = await delete_cgrag_index("old_project")
        >>> if deleted:
        ...     print("Index deleted successfully")
    """
    logger.info(f"Deleting CGRAG index '{name}'")

    index_path = get_index_path(name)
    chunks_path = get_chunks_path(name)
    metadata_path = get_metadata_path(name)

    deleted = False

    for path in [index_path, chunks_path, metadata_path]:
        if path.exists():
            path.unlink()
            logger.info(f"Deleted {path}")
            deleted = True

    if deleted:
        await EventBus.emit("cgrag_index_deleted", {"name": name})

    return deleted


async def get_retriever_for_context(name: str):
    """Get a configured CGRAGRetriever for a specific context.

    Loads the index and returns a retriever ready for queries.
    Returns None if index doesn't exist.

    Args:
        name: Index name

    Returns:
        CGRAGRetriever instance or None

    Example:
        >>> retriever = await get_retriever_for_context("my_project")
        >>> if retriever:
        ...     result = await retriever.retrieve("authentication logic")
    """
    from app.services.cgrag import CGRAGRetriever

    logger.info(f"Loading retriever for context '{name}'")

    index_path = get_index_path(name)
    chunks_path = get_chunks_path(name)
    metadata_path = get_metadata_path(name)

    # Validate all files exist
    if not all(p.exists() for p in [index_path, chunks_path, metadata_path]):
        logger.warning(f"Context '{name}' is incomplete or missing")
        return None

    try:
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata_dict = json.load(f)
        metadata = IndexMetadata(**metadata_dict)

        # Load FAISS index
        index = faiss.read_index(str(index_path))

        # Load chunks
        with open(chunks_path, 'rb') as f:
            chunk_data = pickle.load(f)
        chunks = [DocumentChunk(**data) for data in chunk_data]

        # Create indexer with loaded data
        indexer = CGRAGIndexer(embedding_model=metadata.embedding_model)
        indexer.index = index
        indexer.chunks = chunks

        # Create retriever
        retriever = CGRAGRetriever(indexer=indexer, min_relevance=0.7)

        logger.info(f"Loaded retriever for '{name}': {len(chunks)} chunks")
        return retriever

    except Exception as e:
        logger.error(f"Failed to load retriever for '{name}': {e}")
        return None


def _collect_indexable_files(directory: Path) -> List[Path]:
    """Recursively collect all indexable files in directory.

    Filters by:
    - Supported file extensions (INDEXABLE_EXTENSIONS)
    - Maximum file size (MAX_FILE_SIZE)
    - Excludes hidden files and common ignore patterns

    Args:
        directory: Directory to scan

    Returns:
        List of indexable file paths
    """
    logger.info(f"Scanning {directory} for indexable files")

    # Patterns to ignore
    ignore_patterns = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv',
        'dist', 'build', '.next', '.cache', 'coverage'
    }

    files = []

    for path in directory.rglob('*'):
        # Skip if not a file
        if not path.is_file():
            continue

        # Skip hidden files
        if any(part.startswith('.') for part in path.parts):
            continue

        # Skip ignored directories
        if any(pattern in path.parts for pattern in ignore_patterns):
            continue

        # Check extension
        if path.suffix not in INDEXABLE_EXTENSIONS:
            continue

        # Check file size
        try:
            if path.stat().st_size > MAX_FILE_SIZE:
                logger.debug(f"Skipping {path}: exceeds max file size")
                continue
        except OSError:
            continue

        files.append(path)

    logger.info(f"Found {len(files)} indexable files")
    return sorted(files)
