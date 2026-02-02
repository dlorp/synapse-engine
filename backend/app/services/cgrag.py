"""CGRAG (Contextually-Guided Retrieval Augmented Generation) implementation.

This module provides document indexing and context retrieval using FAISS vector search
with sentence-transformers embeddings. Implements efficient chunking, batched embedding
generation, and token budget management for context retrieval.
"""

import asyncio
import logging
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

import faiss
import numpy as np
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


def get_cgrag_index_paths(index_name: str = "docs") -> Tuple[Path, Path, Path]:
    """Get CGRAG index paths based on runtime settings.

    Args:
        index_name: Name of the index (e.g., "docs", "codebase")

    Returns:
        Tuple of (index_directory, faiss_index_path, metadata_path)

    Example:
        >>> index_dir, index_path, metadata_path = get_cgrag_index_paths("docs")
        >>> # Returns paths like:
        >>> # (data/faiss_indexes, data/faiss_indexes/docs.index, data/faiss_indexes/docs_metadata.pkl)
    """
    from app.services import runtime_settings as settings_service

    # Load runtime settings to get configured directory
    settings = settings_service.get_runtime_settings()

    # Use /app as project root (the Docker working directory)
    # This ensures paths resolve correctly with volume mounts
    project_root = Path("/app")

    # Construct index directory path (relative to project root)
    index_directory = project_root / settings.cgrag_index_directory

    # Construct specific index paths
    faiss_index_path = index_directory / f"{index_name}.index"
    metadata_path = index_directory / f"{index_name}_metadata.pkl"

    return index_directory, faiss_index_path, metadata_path


class DocumentChunk(BaseModel):
    """Represents a document chunk with metadata.

    Attributes:
        id: Unique chunk identifier
        file_path: Path to source document
        content: Chunk text content
        chunk_index: Index of chunk within document
        start_pos: Starting character position in document
        end_pos: Ending character position in document
        language: Detected language (optional)
        modified_time: Source file modification time
        relevance_score: Similarity score from retrieval (0.0-1.0)
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    file_path: str
    content: str
    chunk_index: int
    start_pos: int
    end_pos: int
    language: Optional[str] = None
    modified_time: Optional[datetime] = None
    relevance_score: float = 0.0

    class Config:
        arbitrary_types_allowed = True


class CGRAGResult(BaseModel):
    """Result from CGRAG retrieval operation.

    Attributes:
        artifacts: Retrieved document chunks
        tokens_used: Total tokens in retrieved artifacts
        candidates_considered: Number of candidates before filtering
        retrieval_time_ms: Retrieval operation latency
        cache_hit: Whether result was served from cache
        top_scores: Relevance scores of top artifacts
    """
    artifacts: List[DocumentChunk]
    tokens_used: int
    candidates_considered: int
    retrieval_time_ms: float
    cache_hit: bool = False
    top_scores: List[float] = Field(default_factory=list)


class CGRAGIndexer:
    """Indexes documents into FAISS vector database.

    Creates efficient vector indexes for similarity search using sentence-transformers
    embeddings. Supports multiple file types and implements smart chunking with overlap.

    Attributes:
        encoder: SentenceTransformer model for embeddings
        chunks: List of indexed document chunks
        index: FAISS index for similarity search
        embedding_dim: Dimension of embedding vectors (384 for all-MiniLM-L6-v2)
    """

    # Supported file extensions
    SUPPORTED_EXTENSIONS = {'.md', '.py', '.txt', '.yaml', '.yml', '.json', '.rst'}

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize indexer with sentence-transformers model.

        Args:
            embedding_model: Name of sentence-transformers model to use
        """
        logger.info(f"Initializing CGRAGIndexer with model: {embedding_model}")
        self.embedding_model_name = embedding_model
        self.encoder = SentenceTransformer(embedding_model)
        self.chunks: List[DocumentChunk] = []
        self.index: Optional[faiss.Index] = None
        self.embedding_dim = self.encoder.get_sentence_embedding_dimension()

    async def index_directory(
        self,
        directory: Path,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        batch_size: int = 32
    ) -> int:
        """Recursively index all documents in directory.

        Scans directory for supported file types, chunks documents with overlap,
        generates embeddings in batches, and builds FAISS index.

        Args:
            directory: Root directory to index
            chunk_size: Target chunk size in words
            chunk_overlap: Overlap between chunks in words
            batch_size: Batch size for embedding generation

        Returns:
            Number of chunks indexed

        Raises:
            ValueError: If directory does not exist
        """
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        logger.info(f"Starting indexing of directory: {directory}")
        start_time = time.time()

        # Collect all supported files
        files = self._collect_files(directory)
        logger.info(f"Found {len(files)} supported files")

        # Process files and create chunks
        all_chunks = []
        for file_path in files:
            try:
                chunks = await self._chunk_file(file_path, chunk_size, chunk_overlap)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")

        logger.info(f"Created {len(all_chunks)} chunks from {len(files)} files")

        # Generate embeddings in batches
        embeddings = await self._generate_embeddings_batched(all_chunks, batch_size)

        # Build FAISS index
        self.chunks = all_chunks
        self.index = self._build_faiss_index(embeddings)

        elapsed = time.time() - start_time
        logger.info(
            f"Indexing complete: {len(all_chunks)} chunks in {elapsed:.2f}s "
            f"({len(all_chunks)/elapsed:.1f} chunks/sec)"
        )

        return len(all_chunks)

    def _collect_files(self, directory: Path) -> List[Path]:
        """Recursively collect all supported files in directory.

        Args:
            directory: Directory to scan

        Returns:
            List of file paths
        """
        files = []
        for path in directory.rglob('*'):
            if path.is_file() and path.suffix in self.SUPPORTED_EXTENSIONS:
                files.append(path)
        return sorted(files)

    async def _chunk_file(
        self,
        file_path: Path,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[DocumentChunk]:
        """Read and chunk a single file.

        Args:
            file_path: Path to file
            chunk_size: Target chunk size in words
            chunk_overlap: Overlap in words

        Returns:
            List of document chunks
        """
        # Read file content
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try latin-1 as fallback
            content = file_path.read_text(encoding='latin-1')

        # Get file metadata
        stats = file_path.stat()
        modified_time = datetime.fromtimestamp(stats.st_mtime)

        # Split into words
        words = content.split()

        # Create overlapping chunks
        chunks = []
        start_word_idx = 0
        chunk_index = 0

        while start_word_idx < len(words):
            # Extract chunk words
            end_word_idx = min(start_word_idx + chunk_size, len(words))
            chunk_words = words[start_word_idx:end_word_idx]
            chunk_content = ' '.join(chunk_words)

            # Calculate character positions (approximate)
            start_pos = len(' '.join(words[:start_word_idx]))
            end_pos = start_pos + len(chunk_content)

            # Create chunk
            chunk = DocumentChunk(
                file_path=str(file_path),
                content=chunk_content,
                chunk_index=chunk_index,
                start_pos=start_pos,
                end_pos=end_pos,
                language=self._detect_language(file_path.suffix),
                modified_time=modified_time
            )
            chunks.append(chunk)

            # Move to next chunk with overlap
            if end_word_idx >= len(words):
                break
            start_word_idx += (chunk_size - chunk_overlap)
            chunk_index += 1

        return chunks

    def _detect_language(self, extension: str) -> Optional[str]:
        """Detect language from file extension.

        Args:
            extension: File extension

        Returns:
            Language identifier or None
        """
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.md': 'markdown',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.rst': 'restructuredtext'
        }
        return language_map.get(extension)

    async def _generate_embeddings_batched(
        self,
        chunks: List[DocumentChunk],
        batch_size: int
    ) -> np.ndarray:
        """Generate embeddings for chunks in batches.

        Args:
            chunks: Document chunks to embed
            batch_size: Batch size for encoding

        Returns:
            NumPy array of embeddings (n_chunks x embedding_dim)
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks (batch_size={batch_size})")

        # Extract texts
        texts = [chunk.content for chunk in chunks]

        # Generate embeddings in batches
        # Note: encode() already batches internally, but we can still batch our inputs
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            # Run encoding in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            # Create a partial function with show_progress_bar parameter
            def encode_fn():
                return self.encoder.encode(
                            batch_texts,
                            show_progress_bar=False,
                            convert_to_numpy=True
                        )
            batch_embeddings = await loop.run_in_executor(None, encode_fn)
            all_embeddings.append(batch_embeddings)

        # Concatenate all batches
        embeddings = np.vstack(all_embeddings)
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")

        return embeddings

    def _build_faiss_index(self, embeddings: np.ndarray) -> faiss.Index:
        """Build FAISS index from embeddings.

        Uses IndexFlatL2 for exact search (<100k docs) or IndexIVFFlat for
        approximate search (>100k docs). Normalizes embeddings for better
        similarity scores.

        Args:
            embeddings: NumPy array of embeddings (n_chunks x embedding_dim)

        Returns:
            Trained FAISS index
        """
        n_chunks = embeddings.shape[0]
        logger.info(f"Building FAISS index for {n_chunks} chunks")

        # Normalize embeddings to unit length for better L2 distance -> cosine similarity
        # After normalization: L2^2 = 2(1 - cosine_sim)
        faiss.normalize_L2(embeddings)
        logger.info("Normalized embeddings to unit length")

        if n_chunks < 100000:
            # Use flat index for exact search
            index = faiss.IndexFlatL2(self.embedding_dim)
            index.add(embeddings)
            logger.info(f"Built IndexFlatL2 with {index.ntotal} vectors")
        else:
            # Use IVF index for approximate search
            nlist = min(100, int(np.sqrt(n_chunks)))  # Number of clusters
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist)

            # Train index
            logger.info(f"Training IVF index with nlist={nlist}")
            index.train(embeddings)
            index.add(embeddings)
            logger.info(f"Built IndexIVFFlat with {index.ntotal} vectors")

        return index

    def save_index(self, index_path: Path, metadata_path: Path) -> None:
        """Save FAISS index and chunk metadata to disk.

        Args:
            index_path: Path to save FAISS index
            metadata_path: Path to save chunk metadata
        """
        if self.index is None:
            raise ValueError("No index to save. Run index_directory() first.")

        logger.info(f"Saving index to {index_path}")
        logger.info(f"Saving metadata to {metadata_path}")

        # Save FAISS index
        faiss.write_index(self.index, str(index_path))

        # Save chunk metadata with embedding model info
        metadata = {
            "embedding_model_name": self.embedding_model_name,
            "embedding_dim": self.embedding_dim,
            "chunks": [chunk.model_dump() for chunk in self.chunks]
        }
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

        logger.info(f"Saved {len(self.chunks)} chunks with embedding model: {self.embedding_model_name}")

    @classmethod
    def load_index(cls, index_path: Path, metadata_path: Path) -> "CGRAGIndexer":
        """Load FAISS index and metadata from disk.

        Args:
            index_path: Path to FAISS index file
            metadata_path: Path to metadata file

        Returns:
            CGRAGIndexer instance with loaded index

        Raises:
            FileNotFoundError: If index or metadata files not found
        """
        logger.info(f"Loading index from {index_path}")
        logger.info(f"Loading metadata from {metadata_path}")

        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        # Load chunk metadata
        with open(metadata_path, 'rb') as f:
            loaded_data = pickle.load(f)

        # Handle both old format (list of chunks) and new format (dict with metadata)
        if isinstance(loaded_data, dict):
            embedding_model_name = loaded_data.get("embedding_model_name", "all-MiniLM-L6-v2")
            chunk_data = loaded_data.get("chunks", [])
            logger.info(f"Loaded index with embedding model: {embedding_model_name}")
        else:
            # Old format - just a list of chunks
            embedding_model_name = "all-MiniLM-L6-v2"
            chunk_data = loaded_data
            logger.warning("Loading old format index without embedding model metadata")

        # Create indexer instance with the embedding model from metadata
        indexer = cls(embedding_model=embedding_model_name)

        # Load FAISS index
        indexer.index = faiss.read_index(str(index_path))

        # Load chunks
        indexer.chunks = [DocumentChunk(**data) for data in chunk_data]

        logger.info(f"Loaded {len(indexer.chunks)} chunks")

        return indexer

    def validate_embedding_model(self, expected_model: str) -> tuple[bool, str]:
        """Validate that the index's embedding model matches expected model.

        Args:
            expected_model: Expected embedding model name (from runtime settings)

        Returns:
            Tuple of (is_valid, warning_message)
        """
        if self.embedding_model_name != expected_model:
            warning = (
                f"Embedding model mismatch detected! "
                f"Index was built with '{self.embedding_model_name}' but current runtime settings use '{expected_model}'. "
                f"This may cause dimension mismatch errors or poor retrieval quality. "
                f"Consider re-indexing with the current model."
            )
            logger.warning(warning)
            return False, warning
        return True, ""


class CGRAGRetriever:
    """Retrieves relevant context using FAISS similarity search.

    Implements token budget management with greedy packing algorithm.
    Supports Redis caching for embeddings and retrieval results.

    Attributes:
        indexer: CGRAGIndexer with loaded index
        min_relevance: Minimum relevance threshold (0.0-1.0)
    """

    def __init__(
        self,
        indexer: CGRAGIndexer,
        min_relevance: float = 0.7
    ):
        """Initialize retriever with indexer.

        Args:
            indexer: CGRAGIndexer instance with loaded index
            min_relevance: Minimum relevance threshold for filtering
        """
        self.indexer = indexer
        self.min_relevance = min_relevance

        if self.indexer.index is None:
            raise ValueError("Indexer has no index. Load or build index first.")

    async def retrieve(
        self,
        query: str,
        token_budget: int = 8000,
        max_artifacts: int = 20
    ) -> CGRAGResult:
        """Retrieve relevant artifacts within token budget.

        Searches FAISS index for similar chunks, filters by relevance,
        and packs within token budget using greedy algorithm.

        Args:
            query: Query text
            token_budget: Maximum tokens to retrieve
            max_artifacts: Maximum number of artifacts to consider

        Returns:
            CGRAGResult with artifacts and metadata
        """
        start_time = time.time()

        # Embed query
        loop = asyncio.get_event_loop()
        def encode_fn():
            return self.indexer.encoder.encode(
                    [query],
                    show_progress_bar=False,
                    convert_to_numpy=True
                )
        query_embedding = await loop.run_in_executor(None, encode_fn)
        query_embedding = query_embedding[0].reshape(1, -1)

        # Normalize query embedding to match indexed embeddings
        faiss.normalize_L2(query_embedding)

        # Search FAISS index (retrieve more candidates for filtering)
        k = min(max_artifacts * 5, len(self.indexer.chunks))
        distances, indices = self.indexer.index.search(query_embedding, k)

        # Convert normalized L2 distances to cosine similarity scores
        # For normalized vectors: L2^2 = 2(1 - cosine_sim)
        # Therefore: cosine_sim = 1 - (L2^2 / 2)
        # Note: IndexFlatL2 returns SQUARED L2 distances, so we use them directly
        relevance_scores = 1.0 - (distances[0] / 2.0)

        # Create candidate chunks with relevance scores
        candidates = []
        for idx, score in zip(indices[0], relevance_scores):
            if idx >= 0 and idx < len(self.indexer.chunks):  # Valid index
                chunk = self.indexer.chunks[idx].model_copy()
                chunk.relevance_score = float(score)
                candidates.append(chunk)

        # Filter by minimum relevance
        candidates = [c for c in candidates if c.relevance_score >= self.min_relevance]

        # Pack within token budget
        selected_chunks, tokens_used = self._pack_artifacts(candidates, token_budget)

        # Get top scores
        top_scores = [c.relevance_score for c in selected_chunks]

        elapsed_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Retrieved {len(selected_chunks)} artifacts "
            f"({tokens_used}/{token_budget} tokens) in {elapsed_ms:.1f}ms"
        )

        return CGRAGResult(
            artifacts=selected_chunks,
            tokens_used=tokens_used,
            candidates_considered=len(candidates),
            retrieval_time_ms=elapsed_ms,
            cache_hit=False,
            top_scores=top_scores
        )

    def _pack_artifacts(
        self,
        candidates: List[DocumentChunk],
        token_budget: int
    ) -> Tuple[List[DocumentChunk], int]:
        """Pack artifacts within token budget using greedy algorithm.

        Sorts candidates by relevance and adds chunks until budget is exhausted.

        Args:
            candidates: Candidate chunks with relevance scores
            token_budget: Maximum tokens to use

        Returns:
            Tuple of (selected_chunks, total_tokens_used)
        """
        # Sort by relevance score (descending)
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.relevance_score,
            reverse=True
        )

        selected = []
        total_tokens = 0

        for chunk in sorted_candidates:
            chunk_tokens = self._count_tokens(chunk.content)

            # Check if adding this chunk would exceed budget
            if total_tokens + chunk_tokens > token_budget:
                # If we have no chunks yet, add this one anyway (ensure at least 1 chunk)
                if not selected:
                    selected.append(chunk)
                    total_tokens += chunk_tokens
                break

            selected.append(chunk)
            total_tokens += chunk_tokens

        return selected, total_tokens

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using simple word-based approximation.

        Uses the heuristic: tokens ≈ words * 1.3
        This is a reasonable approximation for English text.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        words = len(text.split())
        return int(words * 1.3)
