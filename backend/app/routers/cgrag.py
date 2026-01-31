"""CGRAG (Contextually-Guided RAG) management endpoints.

This module provides REST API endpoints for managing the CGRAG indexing system,
including triggering indexing operations and checking index status.

Author: Backend Architect
Feature: CGRAG Index Management
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.cgrag import CGRAGIndexer, get_cgrag_index_paths

logger = get_logger(__name__)

router = APIRouter(prefix="/api/cgrag", tags=["cgrag"])

# Track indexing status
_indexing_status = {
    "is_indexing": False,
    "progress": 0,
    "total_files": 0,
    "current_file": None,
    "error": None,
    "last_indexed": None,
}


class IndexRequest(BaseModel):
    """Request to index a directory."""
    directory: str = Field(
        default="/app/docs",
        description="Directory path to index (relative to container or absolute)"
    )
    chunk_size: int = Field(default=512, ge=100, le=2000, description="Target chunk size in words")
    chunk_overlap: int = Field(default=50, ge=0, le=200, description="Overlap between chunks in words")


class IndexStatus(BaseModel):
    """Status of the CGRAG index."""
    index_exists: bool
    chunks_indexed: int
    index_size_mb: float
    last_indexed: Optional[str]
    is_indexing: bool
    indexing_progress: int
    indexing_total: int
    indexing_current_file: Optional[str]
    indexing_error: Optional[str]
    supported_extensions: list[str]


class IndexResponse(BaseModel):
    """Response from indexing operation."""
    success: bool
    message: str
    chunks_indexed: int = 0


@router.get(
    "/status",
    response_model=IndexStatus,
    summary="Get CGRAG index status",
    description="Returns current status of the CGRAG vector index including chunk count and indexing progress."
)
async def get_index_status() -> IndexStatus:
    """Get current CGRAG index status.

    Returns information about the index including whether it exists,
    number of chunks, and any ongoing indexing operation.
    """
    try:
        index_dir, index_path, metadata_path = get_cgrag_index_paths("docs")

        index_exists = index_path.exists() and metadata_path.exists()
        chunks_indexed = 0
        index_size_mb = 0.0

        if index_exists:
            # Get index file size
            index_size_mb = index_path.stat().st_size / (1024 * 1024)

            # Load metadata to get chunk count
            try:
                import pickle
                with open(metadata_path, 'rb') as f:
                    chunks = pickle.load(f)
                    chunks_indexed = len(chunks)
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")

        return IndexStatus(
            index_exists=index_exists,
            chunks_indexed=chunks_indexed,
            index_size_mb=round(index_size_mb, 2),
            last_indexed=_indexing_status.get("last_indexed"),
            is_indexing=_indexing_status["is_indexing"],
            indexing_progress=_indexing_status["progress"],
            indexing_total=_indexing_status["total_files"],
            indexing_current_file=_indexing_status["current_file"],
            indexing_error=_indexing_status["error"],
            supported_extensions=list(CGRAGIndexer.SUPPORTED_EXTENSIONS)
        )

    except Exception as e:
        logger.error(f"Failed to get index status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _run_indexing(directory: str, chunk_size: int, chunk_overlap: int):
    """Background task to run indexing operation."""
    global _indexing_status

    try:
        _indexing_status["is_indexing"] = True
        _indexing_status["error"] = None
        _indexing_status["progress"] = 0

        dir_path = Path(directory)

        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        # Count files first
        files = list(dir_path.rglob("*"))
        supported_files = [
            f for f in files
            if f.is_file() and f.suffix in CGRAGIndexer.SUPPORTED_EXTENSIONS
        ]
        _indexing_status["total_files"] = len(supported_files)

        logger.info(f"Starting CGRAG indexing of {directory} ({len(supported_files)} files)")

        # Create indexer and run indexing
        indexer = CGRAGIndexer()
        chunks_count = await indexer.index_directory(
            directory=dir_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Save index
        index_dir, index_path, metadata_path = get_cgrag_index_paths("docs")
        index_dir.mkdir(parents=True, exist_ok=True)
        indexer.save_index(index_path, metadata_path)

        _indexing_status["progress"] = _indexing_status["total_files"]
        _indexing_status["last_indexed"] = str(Path(directory).name)

        logger.info(f"CGRAG indexing complete: {chunks_count} chunks indexed")

    except Exception as e:
        logger.error(f"CGRAG indexing failed: {e}", exc_info=True)
        _indexing_status["error"] = str(e)

    finally:
        _indexing_status["is_indexing"] = False
        _indexing_status["current_file"] = None


@router.post(
    "/index",
    response_model=IndexResponse,
    summary="Start CGRAG indexing",
    description="Triggers indexing of a directory into the CGRAG vector index. Runs in background."
)
async def start_indexing(
    request: IndexRequest,
    background_tasks: BackgroundTasks
) -> IndexResponse:
    """Start indexing a directory into CGRAG.

    This operation runs in the background. Check /status endpoint for progress.

    Args:
        request: Indexing configuration
        background_tasks: FastAPI background tasks handler

    Returns:
        Response indicating whether indexing was started
    """
    if _indexing_status["is_indexing"]:
        raise HTTPException(
            status_code=409,
            detail="Indexing already in progress. Check /status for progress."
        )

    # Validate directory exists
    dir_path = Path(request.directory)
    if not dir_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Directory does not exist: {request.directory}"
        )

    # Start indexing in background
    background_tasks.add_task(
        _run_indexing,
        request.directory,
        request.chunk_size,
        request.chunk_overlap
    )

    return IndexResponse(
        success=True,
        message=f"Indexing started for {request.directory}. Check /api/cgrag/status for progress."
    )


@router.get(
    "/directories",
    summary="List available directories for indexing",
    description="Returns a list of directories that can be indexed."
)
async def list_indexable_directories() -> dict:
    """List directories available for indexing.

    Returns common directories that users might want to index.
    """
    directories = []

    # Check common locations
    common_paths = [
        ("/app/docs", "Project Documentation"),
        ("/app/backend", "Backend Source Code"),
        ("/app/frontend/src", "Frontend Source Code"),
    ]

    for path, description in common_paths:
        dir_path = Path(path)
        if dir_path.exists():
            # Count indexable files
            files = list(dir_path.rglob("*"))
            indexable = [
                f for f in files
                if f.is_file() and f.suffix in CGRAGIndexer.SUPPORTED_EXTENSIONS
            ]
            directories.append({
                "path": path,
                "description": description,
                "file_count": len(indexable),
                "exists": True
            })
        else:
            directories.append({
                "path": path,
                "description": description,
                "file_count": 0,
                "exists": False
            })

    return {
        "directories": directories,
        "supported_extensions": list(CGRAGIndexer.SUPPORTED_EXTENSIONS)
    }
