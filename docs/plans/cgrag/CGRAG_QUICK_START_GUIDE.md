# CGRAG Enhancement Quick Start Guide

**For the Next Engineer**

This guide helps you get started implementing CGRAG enhancements immediately.

---

## TL;DR - What to Build

You're enhancing the CGRAG (Contextually-Guided RAG) system with:

1. **Better Chunks:** Add document titles, section breadcrumbs, code context to every chunk
2. **Smarter Chunking:** Chunk by document structure (sections, functions) not just word count
3. **Context Enrichment:** Add related chunks from same section, surrounding chunks for continuity
4. **Quality Verification:** Check if retrieval is good enough, reformulate query if not
5. **Infrastructure:** Hybrid search (vector + keywords), knowledge graphs, multiple context sources

**Expected Impact:** +20-25% accuracy, <65ms retrieval latency, <3% hallucinations

---

## Before You Start

### 1. Read These Docs (Priority Order)

1. **[SESSION_NOTES.md](../../SESSION_NOTES.md)** - Read sessions from 2025-11-30 (newest first)
2. **[CGRAG Context Enhancement Design](./CGRAG_CONTEXT_ENHANCEMENT_DESIGN.md)** - Your main implementation guide
3. **[CGRAG Enhancement Plan](./CGRAG_ENHANCEMENT_PLAN.md)** - Infrastructure enhancements (Phase 2)
4. **[CGRAG Enhancement Roadmap](./CGRAG_ENHANCEMENT_ROADMAP.md)** - Overall strategy

### 2. Understand Current Code

**Key Files:**

```
backend/app/services/cgrag.py           # Current CGRAG implementation
backend/app/models/context.py           # Context allocation models
backend/app/routers/cgrag.py            # CGRAG API endpoints
```

**Current Architecture:**

```
User Query
    ↓
CGRAGRetriever.retrieve()
    ↓
1. Embed query with sentence-transformers
2. Search FAISS index (cosine similarity)
3. Filter by relevance threshold (>0.7)
4. Pack within token budget (greedy algorithm)
    ↓
Return DocumentChunk list
```

**What's Missing:**
- No document metadata (title, section, code context)
- Word-based chunking (no structure awareness)
- No context enrichment (just top-k chunks)
- No quality verification (no retry on poor results)

---

## Implementation Path A: Context Enhancement First (Recommended)

Start here for immediate quality gains with lower risk.

### Week 1: Enhanced Chunk Models

**Goal:** Add rich metadata to chunks without breaking existing code.

**Files to Create:**

```python
# backend/app/models/enriched_chunk.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DocumentMetadata(BaseModel):
    """Document-level metadata."""
    title: str
    description: Optional[str] = None
    document_type: str  # "python", "markdown", etc.
    file_size_bytes: int
    total_chunks: int
    tags: List[str] = []
    author: Optional[str] = None
    last_modified: datetime

class SectionHierarchy(BaseModel):
    """Section breadcrumb info."""
    level: int  # 1-6 for markdown headings
    title: str
    parent: Optional[str] = None
    breadcrumb: str  # "Docs > API > Authentication"

class CodeContext(BaseModel):
    """Code-specific metadata."""
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    docstring: Optional[str] = None
    imports: List[str] = []
    type_signature: Optional[str] = None

class EnrichedDocumentChunk(BaseModel):
    """Enhanced chunk with metadata."""
    # Original fields (copy from DocumentChunk)
    id: str
    file_path: str
    content: str
    chunk_index: int
    start_pos: int
    end_pos: int
    language: Optional[str] = None
    modified_time: Optional[datetime] = None
    relevance_score: float = 0.0

    # NEW: Enhanced metadata
    document_metadata: DocumentMetadata
    section_hierarchy: Optional[SectionHierarchy] = None
    code_context: Optional[CodeContext] = None
    related_chunk_ids: List[str] = []
    semantic_summary: Optional[str] = None
```

**Test It:**

```python
# backend/tests/test_enriched_chunk.py

def test_enriched_chunk_creation():
    doc_metadata = DocumentMetadata(
        title="CGRAG Documentation",
        document_type="markdown",
        file_size_bytes=5000,
        total_chunks=10,
        tags=["rag", "retrieval"],
        last_modified=datetime.now()
    )

    section = SectionHierarchy(
        level=2,
        title="Implementation",
        parent="Architecture",
        breadcrumb="Architecture > Implementation"
    )

    chunk = EnrichedDocumentChunk(
        id="chunk_001",
        file_path="/docs/cgrag.md",
        content="CGRAG uses FAISS for vector search...",
        chunk_index=0,
        start_pos=0,
        end_pos=100,
        document_metadata=doc_metadata,
        section_hierarchy=section
    )

    assert chunk.get_breadcrumb_string() == "Architecture > Implementation"
```

### Week 2: Metadata Extraction

**Goal:** Automatically extract metadata during indexing.

**File to Create:**

```python
# backend/app/services/metadata_extractor.py

import ast
import re
from pathlib import Path
from typing import Optional

class MetadataExtractor:
    """Extract metadata from documents."""

    def extract_document_metadata(
        self,
        file_path: Path,
        content: str
    ) -> DocumentMetadata:
        """Extract document-level metadata."""
        title = self._extract_title(file_path, content)
        description = self._extract_description(content, file_path.suffix)
        tags = self._extract_tags(content, file_path.suffix)

        return DocumentMetadata(
            title=title,
            description=description,
            document_type=file_path.suffix.lstrip('.'),
            file_size_bytes=len(content.encode('utf-8')),
            total_chunks=0,  # Set later
            tags=tags,
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime)
        )

    def _extract_title(self, file_path: Path, content: str) -> str:
        """Extract title from markdown H1 or Python docstring."""
        ext = file_path.suffix

        if ext == '.md':
            # Find first H1
            match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()

        elif ext == '.py':
            # Module docstring first line
            try:
                tree = ast.parse(content)
                docstring = ast.get_docstring(tree)
                if docstring:
                    return docstring.split('\n')[0].strip()
            except SyntaxError:
                pass

        # Fallback: filename
        return file_path.stem.replace('_', ' ').title()

    def extract_section_hierarchy(
        self,
        content: str,
        chunk_start: int,
        file_ext: str
    ) -> Optional[SectionHierarchy]:
        """Extract section breadcrumb for a chunk."""
        if file_ext != '.md':
            return None

        # Find all headings before this chunk
        lines_before = content[:chunk_start].split('\n')
        hierarchy = {}

        for line in lines_before:
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                hierarchy[level] = title
                # Clear lower levels
                for l in range(level + 1, 7):
                    hierarchy.pop(l, None)

        if not hierarchy:
            return None

        # Build breadcrumb
        breadcrumb = " > ".join(
            hierarchy[level] for level in sorted(hierarchy.keys())
        )

        max_level = max(hierarchy.keys())
        return SectionHierarchy(
            level=max_level,
            title=hierarchy[max_level],
            parent=hierarchy.get(max_level - 1),
            breadcrumb=breadcrumb
        )

    def extract_code_context(
        self,
        chunk_content: str
    ) -> Optional[CodeContext]:
        """Extract code context from Python chunk."""
        try:
            tree = ast.parse(chunk_content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return CodeContext(
                        function_name=node.name,
                        docstring=ast.get_docstring(node),
                        type_signature=self._get_signature(node),
                        imports=self._extract_imports(tree)
                    )
                elif isinstance(node, ast.ClassDef):
                    return CodeContext(
                        class_name=node.name,
                        docstring=ast.get_docstring(node),
                        imports=self._extract_imports(tree)
                    )
        except SyntaxError:
            pass

        return None

    def _get_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature."""
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        sig = f"{node.name}({', '.join(args)})"
        if node.returns:
            sig += f" -> {ast.unparse(node.returns)}"
        return sig

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract imports from AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports
```

**Integration:**

Modify `backend/app/services/cgrag.py`:

```python
class EnhancedCGRAGIndexer(CGRAGIndexer):
    """Indexer with metadata enrichment."""

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        super().__init__(embedding_model)
        self.metadata_extractor = MetadataExtractor()

    async def _chunk_file(
        self,
        file_path: Path,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[EnrichedDocumentChunk]:
        """Enhanced chunking with metadata."""
        content = file_path.read_text(encoding='utf-8')

        # Extract document metadata
        doc_metadata = self.metadata_extractor.extract_document_metadata(
            file_path,
            content
        )

        # Word-based chunking (same as before)
        words = content.split()
        chunks = []

        for chunk_idx in range(0, len(words), chunk_size - chunk_overlap):
            chunk_words = words[chunk_idx:chunk_idx + chunk_size]
            chunk_content = ' '.join(chunk_words)
            start_pos = len(' '.join(words[:chunk_idx]))
            end_pos = start_pos + len(chunk_content)

            # Extract section hierarchy
            section = self.metadata_extractor.extract_section_hierarchy(
                content,
                start_pos,
                file_path.suffix
            )

            # Extract code context (if Python)
            code_context = None
            if file_path.suffix == '.py':
                code_context = self.metadata_extractor.extract_code_context(
                    chunk_content
                )

            # Create enriched chunk
            chunk = EnrichedDocumentChunk(
                id=str(uuid4()),
                file_path=str(file_path),
                content=chunk_content,
                chunk_index=len(chunks),
                start_pos=start_pos,
                end_pos=end_pos,
                language=self._detect_language(file_path.suffix),
                modified_time=datetime.fromtimestamp(file_path.stat().st_mtime),
                document_metadata=doc_metadata,
                section_hierarchy=section,
                code_context=code_context
            )

            chunks.append(chunk)

        # Update total chunks
        doc_metadata.total_chunks = len(chunks)

        return chunks
```

**Test It:**

```bash
# Re-index documentation with enhanced metadata
python -m backend.scripts.index_documents docs/ --use-enhanced
```

### Week 3: Semantic Chunking

**Goal:** Chunk by structure (sections, functions) not just word count.

See full implementation in [CGRAG_CONTEXT_ENHANCEMENT_DESIGN.md](./CGRAG_CONTEXT_ENHANCEMENT_DESIGN.md#21-semantic-chunking-strategy).

**Key Idea:**

```python
class SemanticChunker:
    def chunk_markdown(self, content: str) -> List[Tuple[str, int, int]]:
        """Chunk markdown by sections (H1-H6)."""
        # Split on headings, keep complete sections together
        # Don't split mid-section unless >max_chunk_size

    def chunk_python(self, content: str) -> List[Tuple[str, int, int]]:
        """Chunk Python by functions/classes."""
        # Parse AST, extract complete function/class definitions
        # Each function/class = one chunk
```

### Week 4: Context Enrichment + Self-RAG

**Goal:** Add related chunks and verify quality.

**Context Enrichment:**

```python
class ContextEnricher:
    def enrich_results(
        self,
        retrieved_chunks: List[EnrichedDocumentChunk],
        max_related: int = 3
    ) -> List[EnrichedDocumentChunk]:
        """Add surrounding chunks and same-section chunks."""
        enriched = []

        for chunk in retrieved_chunks:
            # Add original chunk
            enriched.append(chunk)

            # Add surrounding chunks (±1 index)
            surrounding = self._get_surrounding_chunks(chunk, window=1)
            enriched.extend(surrounding[:max_related])

            # Add high-relevance chunks from same section
            if chunk.section_hierarchy:
                section_chunks = self._get_section_chunks(
                    chunk.section_hierarchy.breadcrumb
                )
                enriched.extend(
                    [c for c in section_chunks if c.relevance_score > 0.7][:max_related]
                )

        return self._deduplicate(enriched)
```

**Self-RAG Quality Verification:**

```python
class SelfRAGVerifier:
    async def retrieve_with_verification(
        self,
        query: str,
        retriever: CGRAGRetriever,
        **kwargs
    ) -> Tuple[List[EnrichedDocumentChunk], RelevanceAssessment]:
        """Retrieve with self-correction loop."""
        current_query = query

        for attempt in range(3):  # Max 2 retries
            # Retrieve
            chunks = await retriever.retrieve(current_query, **kwargs)

            # Assess quality
            assessment = self.assess_relevance(current_query, chunks)

            # If good enough, return
            if assessment.is_relevant:
                return chunks, assessment

            # Reformulate query and retry
            current_query = assessment.suggested_reformulation

        return chunks, assessment  # Return best attempt
```

---

## Implementation Path B: Infrastructure Enhancement

If you want to start with infrastructure (hybrid search, knowledge graph), see [CGRAG_ENHANCEMENT_PLAN.md](./CGRAG_ENHANCEMENT_PLAN.md).

**Key Components:**

1. **Vector DB Abstraction** - Support Qdrant (Metal) + FAISS (fallback)
2. **BM25 Hybrid Search** - Combine vector + keyword search with RRF
3. **Knowledge Graph RAG** - Extract entities, build graph, traverse for related chunks
4. **Multi-Context Sources** - Docs + Code + Chat History
5. **AST Code Chunking** - Parse code with tree-sitter

---

## Testing Your Changes

### Unit Tests

```python
# backend/tests/test_metadata_extractor.py

def test_extract_markdown_title():
    content = "# My Document\n\nSome content..."
    extractor = MetadataExtractor()

    metadata = extractor.extract_document_metadata(
        Path("test.md"),
        content
    )

    assert metadata.title == "My Document"
    assert metadata.document_type == "md"

def test_extract_python_function_context():
    content = '''
def my_function(arg: str) -> int:
    """This is a docstring."""
    return 42
'''
    extractor = MetadataExtractor()
    context = extractor.extract_code_context(content)

    assert context.function_name == "my_function"
    assert context.docstring == "This is a docstring."
    assert "str" in context.type_signature
```

### Integration Tests

```python
# backend/tests/test_enhanced_cgrag.py

async def test_enhanced_indexing():
    indexer = EnhancedCGRAGIndexer()

    # Index test directory
    num_chunks = await indexer.index_directory(
        Path("tests/fixtures/docs"),
        use_semantic_chunking=True
    )

    assert num_chunks > 0

    # Check first chunk has metadata
    chunk = indexer.chunks[0]
    assert chunk.document_metadata is not None
    assert chunk.document_metadata.title != ""

    # Check markdown chunks have section hierarchy
    md_chunks = [c for c in indexer.chunks if c.language == "markdown"]
    assert any(c.section_hierarchy is not None for c in md_chunks)

    # Check Python chunks have code context
    py_chunks = [c for c in indexer.chunks if c.language == "python"]
    assert any(c.code_context is not None for c in py_chunks)
```

### Manual Testing

```bash
# Start backend
cd backend
docker-compose up -d synapse_core

# Index documentation with enhanced metadata
curl -X POST http://localhost:8000/api/cgrag/index \
  -H "Content-Type: application/json" \
  -d '{"directory": "/app/docs", "use_enhanced": true}'

# Query with enriched results
curl -X POST http://localhost:8000/api/cgrag/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "How does CGRAG indexing work?", "enrich_context": true}'

# Check chunk metadata in response
# Should see: document_metadata, section_hierarchy, code_context fields
```

---

## Performance Benchmarks

Track these metrics as you implement:

```python
# backend/scripts/benchmark_cgrag.py

import time
from pathlib import Path

async def benchmark_indexing():
    indexer = EnhancedCGRAGIndexer()

    start = time.time()
    num_chunks = await indexer.index_directory(
        Path("docs/"),
        use_semantic_chunking=True
    )
    elapsed = time.time() - start

    throughput = num_chunks / elapsed
    print(f"Indexed {num_chunks} chunks in {elapsed:.2f}s ({throughput:.1f} chunks/sec)")

    # Target: >800 chunks/sec (down from 1000, but acceptable for quality gain)

async def benchmark_retrieval():
    retriever = CGRAGRetriever(indexer)

    queries = [
        "How does CGRAG work?",
        "What is the query routing logic?",
        "Explain the model management system"
    ]

    latencies = []
    for query in queries:
        start = time.time()
        result = await retriever.retrieve(query, token_budget=8000)
        latencies.append((time.time() - start) * 1000)

    avg_latency = sum(latencies) / len(latencies)
    print(f"Average retrieval latency: {avg_latency:.1f}ms")

    # Target: <120ms (up from 100ms, but with enrichment overhead)
```

**Run Benchmarks:**

```bash
python -m backend.scripts.benchmark_cgrag
```

---

## Common Pitfalls

### Pitfall 1: Breaking Existing Indexes

**Problem:** Changing chunk model breaks existing FAISS indexes.

**Solution:**
- Keep backward compatibility - load old `DocumentChunk`, convert to `EnrichedDocumentChunk` on the fly
- OR: Provide migration script to re-index

```python
# Migration approach
@classmethod
def from_document_chunk(cls, old_chunk: DocumentChunk) -> EnrichedDocumentChunk:
    """Convert old chunk to enriched chunk with default metadata."""
    return cls(
        id=old_chunk.id,
        file_path=old_chunk.file_path,
        content=old_chunk.content,
        chunk_index=old_chunk.chunk_index,
        start_pos=old_chunk.start_pos,
        end_pos=old_chunk.end_pos,
        language=old_chunk.language,
        modified_time=old_chunk.modified_time,
        relevance_score=old_chunk.relevance_score,
        document_metadata=DocumentMetadata(
            title=Path(old_chunk.file_path).stem,
            document_type="unknown",
            file_size_bytes=0,
            total_chunks=1,
            last_modified=old_chunk.modified_time or datetime.now()
        )
    )
```

### Pitfall 2: AST Parsing Errors

**Problem:** Invalid Python syntax breaks AST parsing.

**Solution:** Always wrap in try/except, fall back to basic chunking:

```python
try:
    tree = ast.parse(content)
    # Extract code context
except SyntaxError:
    logger.warning(f"Failed to parse {file_path}: syntax error")
    # Fall back to word-based chunking
```

### Pitfall 3: Memory Explosion

**Problem:** Storing full document content in metadata.

**Solution:** Store only previews/summaries:

```python
# BAD: Store entire document
document_metadata.full_content = content  # Could be MB of text

# GOOD: Store only preview
document_metadata.description = content[:200] + "..."
```

---

## Need Help?

**Check These Resources:**

1. **Design Documents:** [docs/plans/](../plans/)
2. **Research Findings:** [docs/research/GLOBAL_RAG_RESEARCH.md](../research/GLOBAL_RAG_RESEARCH.md)
3. **Session Notes:** [SESSION_NOTES.md](../../SESSION_NOTES.md) (newest first)
4. **Current Code:** [backend/app/services/cgrag.py](${PROJECT_DIR}/backend/app/services/cgrag.py)

**Questions?**

Add questions to SESSION_NOTES.md as you work, document solutions for future engineers.

---

**Good luck! The research shows this will significantly improve retrieval quality. You've got this!**
