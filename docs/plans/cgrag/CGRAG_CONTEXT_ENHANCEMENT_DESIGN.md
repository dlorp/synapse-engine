# CGRAG Context Enhancement Design

**Date:** 2025-11-30
**Status:** Design Document - Ready for Implementation
**Estimated Time:** 2-3 weeks (can be integrated with Phase 1-2 of CGRAG Enhancement Plan)
**Depends On:** [CGRAG_ENHANCEMENT_PLAN.md](./CGRAG_ENHANCEMENT_PLAN.md)

---

## Executive Summary

This design implements **Context Enhancement** features based on global RAG research, focusing on:

1. **Enhanced Chunk Metadata** - Document title, section hierarchy, parent summaries
2. **Semantic Chunking** - Replace word-based chunking with semantic boundaries
3. **Context Enrichment at Query Time** - Breadcrumb navigation, related chunks
4. **Self-RAG Quality Mechanism** - Relevance verification and query reformulation

### Expected Improvements

| Metric | Current | Target | Source |
|--------|---------|--------|--------|
| Retrieval Accuracy | ~70% | **85%+** | Chinese research (+15-20%) |
| Context Relevance | Variable | **>0.8** | Self-RAG quality checks |
| Code Retrieval Quality | Fair | **Excellent** | AST + metadata enrichment |
| User Context Understanding | Limited | **Full breadcrumb trail** | Section hierarchy |

---

## Part 1: Enhanced Chunk Metadata

### Research Findings

**From Chinese Research:**
> "Add document title + section to every chunk" → +15-20% accuracy

**From Korean Research (Kakao):**
> "Chunk = maximum unit that can bundle minimum homogeneous meaning"
> High-quality chunks improve search quality dramatically

**From Japanese Research:**
> "Semantic chunking preserves logical document structure"
> RAPTOR method: GMM clustering + LLM-powered summaries

### 1.1 Enhanced DocumentChunk Model

```python
"""Enhanced document chunk model with rich metadata."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Document-level metadata enrichment.

    Provides context about the parent document to improve retrieval
    relevance and user understanding of chunk provenance.

    Attributes:
        title: Document title extracted from filename or header
        description: Brief document summary (first paragraph or docstring)
        document_type: Type classification (markdown, code, yaml, json, etc.)
        file_size_bytes: Original file size
        total_chunks: Total number of chunks in this document
        tags: Extracted tags/keywords for the document
        author: Author extracted from file metadata or header
        last_modified: File modification timestamp
    """
    title: str = Field(..., description="Document title")
    description: Optional[str] = Field(None, description="Brief document summary")
    document_type: str = Field(..., description="File type (markdown, python, etc.)")
    file_size_bytes: int = Field(..., ge=0)
    total_chunks: int = Field(..., ge=1)
    tags: List[str] = Field(default_factory=list)
    author: Optional[str] = Field(None)
    last_modified: datetime


class SectionHierarchy(BaseModel):
    """Hierarchical section information.

    Captures the document structure hierarchy to provide context
    breadcrumbs (e.g., "Architecture > CGRAG > Indexer").

    Attributes:
        level: Heading level (1-6 for markdown, 0 for code context)
        title: Section title text
        parent: Parent section title (None for top-level)
        breadcrumb: Full breadcrumb path (e.g., "Doc > Section > Subsection")
    """
    level: int = Field(..., ge=0, le=6)
    title: str
    parent: Optional[str] = None
    breadcrumb: str = Field(..., description="Full breadcrumb path")


class CodeContext(BaseModel):
    """Code-specific context metadata.

    Provides rich context for code chunks including function/class names,
    docstrings, imports, and type signatures.

    Attributes:
        function_name: Function/method name (if applicable)
        class_name: Class name (if applicable)
        module_path: Module import path (e.g., "app.services.cgrag")
        docstring: Extracted docstring
        imports: List of imports used by this code
        type_signature: Function signature with type hints
        complexity: Cyclomatic complexity score (optional)
    """
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    module_path: Optional[str] = None
    docstring: Optional[str] = None
    imports: List[str] = Field(default_factory=list)
    type_signature: Optional[str] = None
    complexity: Optional[int] = Field(None, ge=0)


class EnrichedDocumentChunk(BaseModel):
    """Enhanced document chunk with rich metadata.

    Extends the basic DocumentChunk with document-level metadata,
    section hierarchy, and code-specific context for improved retrieval
    and user understanding.

    Attributes:
        id: Unique chunk identifier
        file_path: Path to source document
        content: Chunk text content
        chunk_index: Index of chunk within document
        start_pos: Starting character position in document
        end_pos: Ending character position in document
        language: Detected language (python, markdown, etc.)
        modified_time: Source file modification time
        relevance_score: Similarity score from retrieval (0.0-1.0)

        # ENHANCED METADATA
        document_metadata: Document-level context
        section_hierarchy: Section/heading hierarchy
        code_context: Code-specific metadata (if applicable)
        related_chunk_ids: IDs of related chunks (same section, etc.)
        semantic_summary: Brief semantic summary of chunk content
    """
    # Original fields
    id: str = Field(default_factory=lambda: str(uuid4()))
    file_path: str
    content: str
    chunk_index: int
    start_pos: int
    end_pos: int
    language: Optional[str] = None
    modified_time: Optional[datetime] = None
    relevance_score: float = 0.0

    # Enhanced metadata fields
    document_metadata: DocumentMetadata
    section_hierarchy: Optional[SectionHierarchy] = None
    code_context: Optional[CodeContext] = None
    related_chunk_ids: List[str] = Field(default_factory=list)
    semantic_summary: Optional[str] = Field(
        None,
        description="Brief semantic summary (1-2 sentences)",
        max_length=200
    )

    class Config:
        arbitrary_types_allowed = True

    def get_breadcrumb_string(self) -> str:
        """Get human-readable breadcrumb path.

        Returns:
            Breadcrumb string like "Architecture > CGRAG > Indexer"
        """
        if self.section_hierarchy:
            return self.section_hierarchy.breadcrumb
        return self.document_metadata.title

    def get_context_preview(self, max_length: int = 300) -> str:
        """Get enriched context preview for display.

        Combines document title, section, and content preview.

        Args:
            max_length: Maximum length of preview text

        Returns:
            Formatted context preview
        """
        parts = []

        # Add document title
        parts.append(f"📄 {self.document_metadata.title}")

        # Add breadcrumb if available
        if self.section_hierarchy:
            parts.append(f"📍 {self.section_hierarchy.breadcrumb}")

        # Add code context if available
        if self.code_context:
            if self.code_context.class_name and self.code_context.function_name:
                parts.append(
                    f"🔧 {self.code_context.class_name}.{self.code_context.function_name}"
                )
            elif self.code_context.function_name:
                parts.append(f"🔧 {self.code_context.function_name}")

        # Add content preview
        content_preview = self.content[:max_length]
        if len(self.content) > max_length:
            content_preview += "..."
        parts.append(f"\n{content_preview}")

        return "\n".join(parts)
```

### 1.2 Metadata Extraction Service

```python
"""Service for extracting rich metadata from documents."""

import ast
import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime


class MetadataExtractor:
    """Extract rich metadata from documents during indexing.

    Provides methods to extract document titles, section hierarchies,
    code context, and semantic summaries from various file types.
    """

    def __init__(self):
        self.language_patterns = {
            '.py': self._extract_python_metadata,
            '.md': self._extract_markdown_metadata,
            '.yaml': self._extract_yaml_metadata,
            '.yml': self._extract_yaml_metadata,
            '.json': self._extract_json_metadata,
            '.txt': self._extract_text_metadata,
        }

    def extract_document_metadata(
        self,
        file_path: Path,
        content: str
    ) -> DocumentMetadata:
        """Extract document-level metadata.

        Args:
            file_path: Path to the source file
            content: File content

        Returns:
            DocumentMetadata instance
        """
        stats = file_path.stat()
        ext = file_path.suffix

        # Extract title
        title = self._extract_title(file_path, content, ext)

        # Extract description (first paragraph or docstring)
        description = self._extract_description(content, ext)

        # Extract tags/keywords
        tags = self._extract_tags(content, ext)

        # Extract author (from file header or metadata)
        author = self._extract_author(content, ext)

        return DocumentMetadata(
            title=title,
            description=description,
            document_type=ext.lstrip('.'),
            file_size_bytes=stats.st_size,
            total_chunks=0,  # Will be set later during chunking
            tags=tags,
            author=author,
            last_modified=datetime.fromtimestamp(stats.st_mtime)
        )

    def _extract_title(self, file_path: Path, content: str, ext: str) -> str:
        """Extract document title.

        Priority:
        1. First H1 heading (markdown)
        2. Module docstring first line (Python)
        3. Filename without extension
        """
        if ext == '.md':
            # Look for first H1
            match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()

        elif ext == '.py':
            # Extract from module docstring
            try:
                module = ast.parse(content)
                docstring = ast.get_docstring(module)
                if docstring:
                    # First line of docstring
                    first_line = docstring.split('\n')[0].strip()
                    if first_line:
                        return first_line
            except SyntaxError:
                pass

        # Fallback: filename without extension
        return file_path.stem.replace('_', ' ').replace('-', ' ').title()

    def _extract_description(self, content: str, ext: str) -> Optional[str]:
        """Extract brief document description."""
        if ext == '.md':
            # First paragraph after title
            lines = content.split('\n')
            description_lines = []
            in_description = False

            for line in lines:
                if line.startswith('#'):
                    in_description = True
                    continue

                if in_description and line.strip():
                    description_lines.append(line.strip())
                    if len(' '.join(description_lines)) > 200:
                        break
                elif in_description and not line.strip() and description_lines:
                    break

            if description_lines:
                return ' '.join(description_lines)[:200]

        elif ext == '.py':
            # Module docstring
            try:
                module = ast.parse(content)
                docstring = ast.get_docstring(module)
                if docstring:
                    # Get first paragraph
                    first_para = docstring.split('\n\n')[0]
                    return first_para.strip()[:200]
            except SyntaxError:
                pass

        return None

    def _extract_tags(self, content: str, ext: str) -> List[str]:
        """Extract tags/keywords from content."""
        tags = set()

        if ext == '.py':
            # Common Python keywords that indicate purpose
            keywords = ['async', 'class', 'def', 'import', 'from']
            for keyword in keywords:
                if keyword in content:
                    tags.add(keyword)

            # Extract common patterns
            if 'FastAPI' in content or 'from fastapi' in content:
                tags.add('api')
            if 'async def' in content:
                tags.add('async')
            if 'class ' in content:
                tags.add('class')

        elif ext == '.md':
            # Look for tags/keywords in metadata block
            yaml_block = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
            if yaml_block:
                yaml_content = yaml_block.group(1)
                tag_match = re.search(r'tags:\s*\[(.*?)\]', yaml_content)
                if tag_match:
                    tag_str = tag_match.group(1)
                    tags.update(t.strip().strip('"\'') for t in tag_str.split(','))

        return sorted(list(tags))

    def _extract_author(self, content: str, ext: str) -> Optional[str]:
        """Extract author from file header or metadata."""
        # Look for common author patterns
        patterns = [
            r'Author:\s*(.+)',
            r'@author\s+(.+)',
            r'Created by:\s*(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_python_metadata(
        self,
        content: str,
        chunk: str,
        chunk_start: int
    ) -> Optional[CodeContext]:
        """Extract Python-specific code context."""
        try:
            # Parse the chunk
            tree = ast.parse(chunk)

            # Find function/class definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return CodeContext(
                        function_name=node.name,
                        docstring=ast.get_docstring(node),
                        type_signature=self._get_function_signature(node),
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

    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature with type hints."""
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
        """Extract import statements from AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return imports

    def _extract_markdown_metadata(
        self,
        content: str,
        chunk: str,
        chunk_start: int
    ) -> Optional[SectionHierarchy]:
        """Extract markdown section hierarchy."""
        # Find all headings before this chunk
        headings_before = []
        lines_before = content[:chunk_start].split('\n')

        current_hierarchy = {}

        for line in lines_before:
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                # Update hierarchy
                current_hierarchy[level] = title
                # Clear lower levels
                for l in range(level + 1, 7):
                    current_hierarchy.pop(l, None)

        if not current_hierarchy:
            return None

        # Build breadcrumb
        breadcrumb_parts = []
        for level in sorted(current_hierarchy.keys()):
            breadcrumb_parts.append(current_hierarchy[level])

        breadcrumb = " > ".join(breadcrumb_parts)

        # Get current section (lowest level)
        max_level = max(current_hierarchy.keys())

        return SectionHierarchy(
            level=max_level,
            title=current_hierarchy[max_level],
            parent=current_hierarchy.get(max_level - 1),
            breadcrumb=breadcrumb
        )

    def _extract_yaml_metadata(
        self,
        content: str,
        chunk: str,
        chunk_start: int
    ) -> Optional[SectionHierarchy]:
        """Extract YAML section context."""
        # For YAML, use top-level keys as sections
        lines = content[:chunk_start].split('\n')
        current_section = None

        for line in lines:
            if line and not line.startswith(' ') and ':' in line:
                current_section = line.split(':')[0].strip()

        if current_section:
            return SectionHierarchy(
                level=1,
                title=current_section,
                parent=None,
                breadcrumb=current_section
            )

        return None

    def _extract_json_metadata(
        self,
        content: str,
        chunk: str,
        chunk_start: int
    ) -> Optional[SectionHierarchy]:
        """Extract JSON context (top-level keys)."""
        # Similar to YAML
        return self._extract_yaml_metadata(content, chunk, chunk_start)

    def _extract_text_metadata(
        self,
        content: str,
        chunk: str,
        chunk_start: int
    ) -> None:
        """Plain text has no special metadata."""
        return None
```

---

## Part 2: Semantic Chunking

### Research Findings

**From Korean Research (Kakao):**
> "Chunk = maximum unit that can bundle minimum homogeneous meaning"
> "High-quality chunks improve search quality dramatically"
> "Focus strongly on single topic per chunk"

**From Japanese Research:**
> "Semantic chunking preserves logical document structure"
> "RAPTOR method: GMM clustering + LLM-powered summaries"

**From Chinese Research:**
> "Context Enhancement: add document title + section to every chunk"

### 2.1 Semantic Chunking Strategy

```python
"""Semantic chunking that preserves document structure."""

from typing import List
import re


class SemanticChunker:
    """Create semantically meaningful chunks.

    Instead of word-based chunking, preserves:
    - Markdown sections (based on headings)
    - Code blocks (functions, classes)
    - Logical paragraphs
    - List items as groups
    """

    def __init__(
        self,
        target_chunk_size: int = 512,
        max_chunk_size: int = 1024,
        min_chunk_size: int = 100
    ):
        """Initialize semantic chunker.

        Args:
            target_chunk_size: Target size in words
            max_chunk_size: Maximum size before forced split
            min_chunk_size: Minimum size (merge small chunks)
        """
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def chunk_markdown(self, content: str) -> List[Tuple[str, int, int]]:
        """Chunk markdown by semantic boundaries.

        Preserves:
        - Complete sections (heading + content)
        - Code blocks as single units
        - Paragraph boundaries

        Args:
            content: Markdown content

        Returns:
            List of (chunk_text, start_pos, end_pos) tuples
        """
        chunks = []
        current_chunk = []
        current_size = 0
        current_start = 0

        # Split by sections
        sections = re.split(r'(^#{1,6}\s+.+$)', content, flags=re.MULTILINE)

        for i, section in enumerate(sections):
            if not section.strip():
                continue

            section_size = len(section.split())

            # If this is a heading, start new chunk if current is not empty
            if re.match(r'^#{1,6}\s+', section):
                if current_chunk and current_size > self.min_chunk_size:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append((
                        chunk_text,
                        current_start,
                        current_start + len(chunk_text)
                    ))
                    current_chunk = []
                    current_size = 0

                current_chunk.append(section)
                current_size += section_size
                current_start = content.find(section)

            # If adding this section would exceed max size, flush current chunk
            elif current_size + section_size > self.max_chunk_size:
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append((
                        chunk_text,
                        current_start,
                        current_start + len(chunk_text)
                    ))

                # Start new chunk with current section
                current_chunk = [section]
                current_size = section_size
                current_start = content.find(section, current_start)

            # Otherwise add to current chunk
            else:
                current_chunk.append(section)
                current_size += section_size

            # If we've reached target size and next item is a heading, flush
            if current_size >= self.target_chunk_size:
                if i + 1 < len(sections) and re.match(r'^#{1,6}\s+', sections[i + 1]):
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append((
                        chunk_text,
                        current_start,
                        current_start + len(chunk_text)
                    ))
                    current_chunk = []
                    current_size = 0

        # Flush remaining
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append((
                chunk_text,
                current_start,
                current_start + len(chunk_text)
            ))

        return chunks

    def chunk_python(self, content: str) -> List[Tuple[str, int, int]]:
        """Chunk Python code by semantic boundaries.

        Preserves:
        - Complete function definitions
        - Complete class definitions
        - Module docstrings as separate chunks

        Args:
            content: Python source code

        Returns:
            List of (chunk_text, start_pos, end_pos) tuples
        """
        try:
            tree = ast.parse(content)
            chunks = []

            # Extract module docstring as first chunk
            docstring = ast.get_docstring(tree)
            if docstring:
                doc_end = content.find(docstring) + len(docstring) + 6  # Account for quotes
                chunks.append((docstring, 0, doc_end))

            # Extract top-level functions and classes
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start_line = node.lineno - 1
                    end_line = node.end_lineno

                    lines = content.split('\n')
                    chunk_lines = lines[start_line:end_line]
                    chunk_text = '\n'.join(chunk_lines)

                    # Calculate byte positions
                    start_pos = len('\n'.join(lines[:start_line]))
                    end_pos = start_pos + len(chunk_text)

                    chunks.append((chunk_text, start_pos, end_pos))

            # If no semantic chunks found, fall back to size-based
            if not chunks:
                return self._fallback_chunk(content)

            return chunks

        except SyntaxError:
            # Fall back to size-based chunking for invalid Python
            return self._fallback_chunk(content)

    def _fallback_chunk(
        self,
        content: str
    ) -> List[Tuple[str, int, int]]:
        """Fallback to word-based chunking."""
        chunks = []
        words = content.split()

        for i in range(0, len(words), self.target_chunk_size):
            chunk_words = words[i:i + self.target_chunk_size]
            chunk_text = ' '.join(chunk_words)

            # Calculate positions
            start_pos = len(' '.join(words[:i]))
            end_pos = start_pos + len(chunk_text)

            chunks.append((chunk_text, start_pos, end_pos))

        return chunks
```

---

## Part 3: Context Enrichment at Query Time

### 3.1 Related Chunk Retrieval

```python
"""Context enrichment with related chunks."""

from typing import List, Set


class ContextEnricher:
    """Enrich retrieved chunks with related context.

    Adds:
    - Parent document summary
    - Chunks from same section
    - Surrounding chunks for continuity
    """

    def __init__(self, all_chunks: List[EnrichedDocumentChunk]):
        """Initialize context enricher.

        Args:
            all_chunks: All available chunks for context lookup
        """
        self.all_chunks = all_chunks
        self.chunks_by_file = self._index_by_file()
        self.chunks_by_section = self._index_by_section()

    def _index_by_file(self) -> dict:
        """Index chunks by file path."""
        index = {}
        for chunk in self.all_chunks:
            if chunk.file_path not in index:
                index[chunk.file_path] = []
            index[chunk.file_path].append(chunk)

        # Sort by chunk_index
        for file_path in index:
            index[file_path].sort(key=lambda c: c.chunk_index)

        return index

    def _index_by_section(self) -> dict:
        """Index chunks by section breadcrumb."""
        index = {}
        for chunk in self.all_chunks:
            if chunk.section_hierarchy:
                breadcrumb = chunk.section_hierarchy.breadcrumb
                if breadcrumb not in index:
                    index[breadcrumb] = []
                index[breadcrumb].append(chunk)

        return index

    def enrich_results(
        self,
        retrieved_chunks: List[EnrichedDocumentChunk],
        max_related: int = 3
    ) -> List[EnrichedDocumentChunk]:
        """Enrich retrieved chunks with related context.

        For each retrieved chunk, adds:
        - Immediately surrounding chunks (±1 chunk index)
        - Other high-relevance chunks from same section

        Args:
            retrieved_chunks: Initially retrieved chunks
            max_related: Maximum related chunks to add per result

        Returns:
            Enriched chunk list (deduplicated)
        """
        enriched = []
        seen_ids: Set[str] = set()

        for chunk in retrieved_chunks:
            # Add original chunk
            if chunk.id not in seen_ids:
                enriched.append(chunk)
                seen_ids.add(chunk.id)

            # Add surrounding chunks (context continuity)
            surrounding = self._get_surrounding_chunks(chunk, window=1)
            for related in surrounding[:max_related]:
                if related.id not in seen_ids:
                    enriched.append(related)
                    seen_ids.add(related.id)

            # Add same-section chunks if highly relevant
            if chunk.section_hierarchy:
                section_chunks = self.chunks_by_section.get(
                    chunk.section_hierarchy.breadcrumb,
                    []
                )
                # Sort by relevance
                section_chunks = sorted(
                    section_chunks,
                    key=lambda c: c.relevance_score,
                    reverse=True
                )
                for related in section_chunks[:max_related]:
                    if related.id not in seen_ids and related.relevance_score > 0.7:
                        enriched.append(related)
                        seen_ids.add(related.id)

        return enriched

    def _get_surrounding_chunks(
        self,
        chunk: EnrichedDocumentChunk,
        window: int = 1
    ) -> List[EnrichedDocumentChunk]:
        """Get chunks surrounding a given chunk.

        Args:
            chunk: Target chunk
            window: Number of chunks before/after to include

        Returns:
            List of surrounding chunks
        """
        file_chunks = self.chunks_by_file.get(chunk.file_path, [])

        # Find current chunk index in file
        try:
            current_idx = next(
                i for i, c in enumerate(file_chunks)
                if c.id == chunk.id
            )
        except StopIteration:
            return []

        # Get surrounding chunks
        start_idx = max(0, current_idx - window)
        end_idx = min(len(file_chunks), current_idx + window + 1)

        surrounding = []
        for i in range(start_idx, end_idx):
            if i != current_idx:
                surrounding.append(file_chunks[i])

        return surrounding
```

---

## Part 4: Self-RAG Quality Mechanism

### Research Findings

**From Chinese Research:**
> "Self-RAG mechanism: quality check → reformulate → retry"

**From Russian Research:**
> "Corrective RAG: Verify relevance before using context"

### 4.1 Relevance Verification

```python
"""Self-RAG quality verification and query reformulation."""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
import numpy as np


class RelevanceAssessment(BaseModel):
    """Assessment of retrieval relevance quality.

    Attributes:
        is_relevant: Whether context is relevant enough
        confidence: Confidence score (0-1)
        reason: Explanation of assessment
        suggested_reformulation: Suggested query reformulation (if low quality)
    """
    is_relevant: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str
    suggested_reformulation: Optional[str] = None


class SelfRAGVerifier:
    """Verify and improve retrieval quality.

    Implements self-correction loop:
    1. Assess relevance of retrieved context
    2. If low quality, reformulate query
    3. Retry retrieval with reformulated query
    4. Return best results
    """

    def __init__(
        self,
        min_avg_relevance: float = 0.7,
        min_top_relevance: float = 0.8,
        max_retries: int = 2
    ):
        """Initialize self-RAG verifier.

        Args:
            min_avg_relevance: Minimum average relevance score
            min_top_relevance: Minimum top result relevance
            max_retries: Maximum reformulation retries
        """
        self.min_avg_relevance = min_avg_relevance
        self.min_top_relevance = min_top_relevance
        self.max_retries = max_retries

    def assess_relevance(
        self,
        query: str,
        chunks: List[EnrichedDocumentChunk]
    ) -> RelevanceAssessment:
        """Assess whether retrieved chunks are relevant enough.

        Checks:
        1. Average relevance score across all chunks
        2. Top result relevance score
        3. Variance in relevance scores (consistency)

        Args:
            query: Original query
            chunks: Retrieved chunks

        Returns:
            RelevanceAssessment with verdict and suggestions
        """
        if not chunks:
            return RelevanceAssessment(
                is_relevant=False,
                confidence=1.0,
                reason="No chunks retrieved",
                suggested_reformulation=self._suggest_reformulation(query, "no_results")
            )

        # Calculate relevance statistics
        scores = [c.relevance_score for c in chunks]
        avg_score = np.mean(scores)
        top_score = max(scores)
        score_variance = np.var(scores)

        # Check quality thresholds
        issues = []

        if top_score < self.min_top_relevance:
            issues.append(f"Top relevance too low ({top_score:.2f} < {self.min_top_relevance})")

        if avg_score < self.min_avg_relevance:
            issues.append(f"Average relevance too low ({avg_score:.2f} < {self.min_avg_relevance})")

        if score_variance > 0.1:  # High variance = inconsistent results
            issues.append(f"High relevance variance ({score_variance:.2f}) - inconsistent results")

        # Determine relevance
        is_relevant = len(issues) == 0

        if is_relevant:
            return RelevanceAssessment(
                is_relevant=True,
                confidence=min(avg_score, top_score),
                reason=f"Good retrieval quality (avg={avg_score:.2f}, top={top_score:.2f})"
            )
        else:
            return RelevanceAssessment(
                is_relevant=False,
                confidence=avg_score,
                reason="; ".join(issues),
                suggested_reformulation=self._suggest_reformulation(
                    query,
                    "low_relevance",
                    avg_score=avg_score
                )
            )

    def _suggest_reformulation(
        self,
        query: str,
        issue_type: str,
        **kwargs
    ) -> str:
        """Suggest query reformulation based on issue.

        Strategies:
        - Add context keywords for low relevance
        - Simplify for no results
        - Add technical terms for code queries

        Args:
            query: Original query
            issue_type: Type of issue (no_results, low_relevance)
            **kwargs: Additional context

        Returns:
            Reformulated query
        """
        if issue_type == "no_results":
            # Simplify query - remove extra words
            words = query.split()
            if len(words) > 5:
                # Keep key nouns and verbs
                return ' '.join(words[:5])
            return query

        elif issue_type == "low_relevance":
            # Add context keywords
            if "code" in query.lower() or "function" in query.lower():
                # Add technical context
                return f"{query} implementation source code"
            elif "how" in query.lower():
                # Add documentation context
                return f"{query} documentation guide"
            else:
                # Generic enhancement
                return f"{query} details explanation"

        return query

    async def retrieve_with_verification(
        self,
        query: str,
        retriever: 'CGRAGRetriever',
        **retriever_kwargs
    ) -> Tuple[List[EnrichedDocumentChunk], RelevanceAssessment]:
        """Retrieve with self-correction loop.

        Process:
        1. Initial retrieval
        2. Assess relevance
        3. If low quality and retries remain, reformulate and retry
        4. Return best results

        Args:
            query: Original query
            retriever: CGRAGRetriever instance
            **retriever_kwargs: Additional retriever arguments

        Returns:
            Tuple of (best_chunks, final_assessment)
        """
        current_query = query
        best_chunks = []
        best_assessment = None

        for attempt in range(self.max_retries + 1):
            # Retrieve chunks
            result = await retriever.retrieve(current_query, **retriever_kwargs)
            chunks = result.artifacts

            # Assess relevance
            assessment = self.assess_relevance(current_query, chunks)

            # Track best results
            if not best_assessment or assessment.confidence > best_assessment.confidence:
                best_chunks = chunks
                best_assessment = assessment

            # If relevant enough, return
            if assessment.is_relevant:
                return chunks, assessment

            # If out of retries, return best
            if attempt >= self.max_retries:
                return best_chunks, best_assessment

            # Reformulate query for next attempt
            if assessment.suggested_reformulation:
                current_query = assessment.suggested_reformulation
                logger.info(
                    f"Self-RAG reformulation (attempt {attempt + 1}): "
                    f"'{query}' -> '{current_query}'"
                )
            else:
                # No reformulation possible, return best
                return best_chunks, best_assessment

        return best_chunks, best_assessment
```

---

## Integration with CGRAGIndexer

### Modified Indexing Pipeline

```python
"""Enhanced CGRAG indexer with context enrichment."""

class EnhancedCGRAGIndexer(CGRAGIndexer):
    """Extended indexer with metadata enrichment and semantic chunking."""

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        super().__init__(embedding_model)
        self.metadata_extractor = MetadataExtractor()
        self.semantic_chunker = SemanticChunker()

    async def index_directory(
        self,
        directory: Path,
        use_semantic_chunking: bool = True,
        batch_size: int = 32
    ) -> int:
        """Index directory with enhanced metadata.

        Args:
            directory: Root directory to index
            use_semantic_chunking: Use semantic chunking vs word-based
            batch_size: Batch size for embedding generation

        Returns:
            Number of chunks indexed
        """
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        logger.info(f"Starting enhanced indexing of directory: {directory}")
        start_time = time.time()

        # Collect all supported files
        files = self._collect_files(directory)
        logger.info(f"Found {len(files)} supported files")

        # Process files with enhanced chunking
        all_chunks = []
        for file_path in files:
            try:
                chunks = await self._chunk_file_enhanced(
                    file_path,
                    use_semantic_chunking
                )
                all_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")

        logger.info(f"Created {len(all_chunks)} enriched chunks from {len(files)} files")

        # Generate embeddings in batches
        embeddings = await self._generate_embeddings_batched(all_chunks, batch_size)

        # Build FAISS index
        self.chunks = all_chunks
        self.index = self._build_faiss_index(embeddings)

        elapsed = time.time() - start_time
        logger.info(
            f"Enhanced indexing complete: {len(all_chunks)} chunks in {elapsed:.2f}s "
            f"({len(all_chunks)/elapsed:.1f} chunks/sec)"
        )

        return len(all_chunks)

    async def _chunk_file_enhanced(
        self,
        file_path: Path,
        use_semantic: bool
    ) -> List[EnrichedDocumentChunk]:
        """Chunk file with enhanced metadata extraction.

        Args:
            file_path: Path to file
            use_semantic: Use semantic chunking

        Returns:
            List of enriched document chunks
        """
        # Read file content
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = file_path.read_text(encoding='latin-1')

        # Extract document metadata
        doc_metadata = self.metadata_extractor.extract_document_metadata(
            file_path,
            content
        )

        # Semantic or word-based chunking
        ext = file_path.suffix
        if use_semantic:
            if ext == '.md':
                chunk_data = self.semantic_chunker.chunk_markdown(content)
            elif ext == '.py':
                chunk_data = self.semantic_chunker.chunk_python(content)
            else:
                # Fallback to word-based
                chunk_data = self.semantic_chunker._fallback_chunk(content)
        else:
            # Original word-based chunking
            chunk_data = self._chunk_file_word_based(file_path, content)

        # Create enriched chunks
        enriched_chunks = []
        for chunk_index, (chunk_content, start_pos, end_pos) in enumerate(chunk_data):
            # Extract section hierarchy
            section_hierarchy = None
            if ext == '.md':
                section_hierarchy = self.metadata_extractor._extract_markdown_metadata(
                    content,
                    chunk_content,
                    start_pos
                )

            # Extract code context
            code_context = None
            if ext == '.py':
                code_context = self.metadata_extractor._extract_python_metadata(
                    content,
                    chunk_content,
                    start_pos
                )

            # Create enriched chunk
            chunk = EnrichedDocumentChunk(
                file_path=str(file_path),
                content=chunk_content,
                chunk_index=chunk_index,
                start_pos=start_pos,
                end_pos=end_pos,
                language=self._detect_language(ext),
                modified_time=datetime.fromtimestamp(file_path.stat().st_mtime),
                document_metadata=doc_metadata,
                section_hierarchy=section_hierarchy,
                code_context=code_context
            )

            enriched_chunks.append(chunk)

        # Update document metadata with total chunk count
        doc_metadata.total_chunks = len(enriched_chunks)

        return enriched_chunks
```

---

## Summary: Implementation Checklist

### Files to Create

| File | Purpose | Lines | Priority |
|------|---------|-------|----------|
| `backend/app/models/enriched_chunk.py` | Enhanced chunk models | ~400 | HIGH |
| `backend/app/services/metadata_extractor.py` | Metadata extraction | ~500 | HIGH |
| `backend/app/services/semantic_chunker.py` | Semantic chunking | ~300 | HIGH |
| `backend/app/services/context_enricher.py` | Context enrichment | ~200 | MEDIUM |
| `backend/app/services/self_rag_verifier.py` | Self-RAG quality checks | ~250 | MEDIUM |

### Files to Modify

| File | Changes | Priority |
|------|---------|----------|
| `backend/app/services/cgrag.py` | Add EnhancedCGRAGIndexer class | HIGH |
| `backend/app/models/context.py` | Update CGRAGArtifact with enriched fields | HIGH |
| `backend/app/routers/cgrag.py` | Add metadata to responses | MEDIUM |

### Testing Checklist

- [ ] Test metadata extraction for all file types (.py, .md, .yaml, .json)
- [ ] Verify semantic chunking preserves logical boundaries
- [ ] Test breadcrumb generation for nested sections
- [ ] Verify code context extraction (function names, docstrings)
- [ ] Test context enrichment (surrounding chunks, same section)
- [ ] Verify self-RAG relevance assessment logic
- [ ] Test query reformulation suggestions
- [ ] Benchmark indexing performance (should match original <100ms retrieval)
- [ ] Validate enriched chunk serialization/deserialization

### Expected Performance Impact

| Metric | Current | With Enhancement | Change |
|--------|---------|------------------|--------|
| Indexing Time | 1000 chunks/sec | 800-900 chunks/sec | -10-20% (acceptable) |
| Retrieval Latency | <100ms | <120ms | +20ms (enrichment overhead) |
| Accuracy | ~70% | **85%+** | **+15%** |
| User Context Understanding | Limited | Excellent | Major improvement |

---

## Related Documentation

- [CGRAG_ENHANCEMENT_PLAN.md](./CGRAG_ENHANCEMENT_PLAN.md) - Main enhancement plan (hybrid search, graph RAG)
- [GLOBAL_RAG_RESEARCH.md](../research/GLOBAL_RAG_RESEARCH.md) - Research findings
- [SESSION_NOTES.md](../../SESSION_NOTES.md) - Development history

---

## Next Steps for Implementation

1. **Phase 1 (Week 1):** Enhanced chunk models and metadata extraction
   - Create `enriched_chunk.py` with new models
   - Implement `metadata_extractor.py`
   - Add unit tests

2. **Phase 2 (Week 2):** Semantic chunking
   - Implement `semantic_chunker.py`
   - Integrate with `EnhancedCGRAGIndexer`
   - Test on documentation and codebase

3. **Phase 3 (Week 3):** Context enrichment and self-RAG
   - Implement `context_enricher.py`
   - Implement `self_rag_verifier.py`
   - Integration testing with full pipeline

4. **Phase 4 (Week 4):** Integration and optimization
   - Update API endpoints to return enriched metadata
   - Frontend integration (display breadcrumbs, context previews)
   - Performance optimization and benchmarking
