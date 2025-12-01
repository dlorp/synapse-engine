# Global RAG Research Report

**Research Date:** 2025-11-30
**Languages Researched:** English, Chinese (中文), Japanese (日本語), Korean (한국어), German (Deutsch), French (Français), Russian (Русский)

---

## Executive Summary

This report synthesizes cutting-edge RAG (Retrieval-Augmented Generation) research from global sources to inform the S.Y.N.A.P.S.E. ENGINE CGRAG enhancement. Key discoveries include:

| Region | Key Innovation | Impact |
|--------|---------------|--------|
| **China** | 2-Stage Reranking, VisRAG, Hyper-RAG | +15-25% accuracy |
| **Japan** | Morphological chunking, DualCSE | CJK text handling |
| **Korea** | AutoRAG optimization, Kakao chunking | Automated tuning |
| **Germany** | Knowledge Graph RAG, GDPR compliance | Reduced hallucinations |
| **France** | Mistral efficiency, RAG Triad evaluation | 17% faster inference |
| **Russia** | Adaptive routing, Corrective RAG | 30-40% cost reduction |

---

## Part 1: Chinese RAG Innovations (中文研究)

### 1.1 Two-Stage Retrieval Revolution (QAnything Pattern)

**Key Insight:** Chinese implementations treat reranking as PRIMARY, not optional.

**The QAnything Pattern (NetEase):**
1. **Stage 1:** Coarse vector retrieval - get top 100 candidates
2. **Stage 2:** Fine-grained reranking with threshold > 0.35

**Performance:** "More data = better results" - opposite of pure vector search logic

**Source:** [QAnything源码解析](https://blog.csdn.net/u013261578/article/details/145353349)

### 1.2 VisRAG - Visual Document Retrieval

**Innovation:** Store documents as **images**, not text chunks.

**Developer:** Tsinghua University & MianWall Intelligence

**Benefits:**
- Preserves formatting, tables, diagrams completely
- **25-39% improvement** over text-only RAG on certain tasks
- Perfect for technical documentation with visual elements

**Source:** [VisRAG详解](https://zhuanlan.zhihu.com/p/2105216542)

### 1.3 Hyper-RAG - Beyond Graphs

**Innovation:** Uses **hypergraphs** instead of regular knowledge graphs.

**Developer:** Tsinghua + Xi'an Jiaotong University

**Key Difference:** Captures group high-order associations, not just pairwise relationships

**Performance:**
- **+12.3% accuracy** vs direct LLM
- **+6.3%** vs standard GraphRAG

**Source:** [Hyper-RAG原理](https://finance.sina.com.cn/tech/csj/2025-04-19/doc-inetspiz0979845.shtml)

### 1.4 Chinese Enterprise Solutions

| Provider | Key Feature | Scale |
|----------|-------------|-------|
| **Alibaba Cloud** | PB-scale RAG platform, 5-10 lines of code integration | Enterprise |
| **Baidu iRAG** | Image-based RAG, 1.5B+ daily API calls | Massive scale |
| **Tencent VectorDB** | 100B vectors, million-level QPS, first to pass China RAG certification | Hyperscale |

### 1.5 Top Chinese Open Source Projects

| Project | Stars | Key Innovation | GitHub |
|---------|-------|----------------|--------|
| **Langchain-Chatchat** | 28.7k | Fully offline Chinese RAG, Apache license | [chatchat-space/Langchain-Chatchat](https://github.com/chatchat-space/Langchain-Chatchat) |
| **QAnything** | - | Industrial 2-stage retrieval, <16GB VRAM | [netease-youdao/QAnything](https://github.com/netease-youdao/QAnything) |
| **RAGFlow** | - | OCR + visualization + Agent capabilities | [infiniflow/ragflow](https://github.com/infiniflow/ragflow) |

### 1.6 Chinese Academic Breakthroughs

**Tsinghua University:**
- **UltraRAG:** 10% better than BGE-M3 on MTEB benchmark
- **DeepNote:** +20.1% performance via "Note" knowledge carriers
- **RAG-DDR:** Accepted to ICLR 2025

**Peking University:**
- Comprehensive 300+ paper RAG survey
- GraphRAG framework analysis

### 1.7 High-Impact Recommendations from Chinese Research

1. **2-Stage Retrieval with Reranking** (+15-20% accuracy)
2. **Hybrid Search** (Vector + BM25) - critical for code/technical queries
3. **Context Enhancement** - add document title + section to every chunk
4. **Self-RAG Mechanism** - quality check → reformulate → retry
5. **GraphRAG for Code** - knowledge graph of codebase relationships

**Performance Targets (Chinese Standards):**

| Metric | Target |
|--------|--------|
| Retrieval Latency | <100ms |
| Cache Hit Rate | >70% |
| Relevance Score | >0.8 |
| Rerank Threshold | >0.35 |
| Indexing Throughput | >1000 chunks/sec |

---

## Part 2: Japanese RAG Innovations (日本語研究)

### 2.1 CJK-Specific Challenges

**Problem:** Japanese has no word boundaries - requires morphological analysis.

**Solution Stack:**
- **Tokenizer:** MeCab, Sudachi for word segmentation
- **Embedding:** Ruri (2024), intfloat/multilingual-e5-large
- **Hybrid Search:** BM25 with MeCab tokenization + vector search

### 2.2 Japanese Chunking Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Morphological Analysis** (形態素解析) | Uses MeCab/Sudachi for word boundaries | Essential for all Japanese text |
| **Semantic Chunking** (セマンティックチャンキング) | Preserves logical document structure | Documentation, reports |
| **MoGG Method** | Handles terminology glossaries, internal regulations | Corporate documents |
| **RAPTOR Method** | GMM clustering + LLM-powered summaries | Large document sets |

**Source:** [RAG入門: 精度改善のための手法28選](https://qiita.com/FukuharaYohei/items/0949aaac17f7b0a4c807)

### 2.3 "Nurutto shita nihongo" Problem (ぬるっとした日本語)

**Challenge:** Japanese expressions where surface meaning differs from true intent.

Standard embedding models struggle with nuanced Japanese expressions.

**Solution:** **DualCSE** - represents single sentence with two separate vectors to capture both literal and implied meaning.

**Source:** [RAGが苦手な「ぬるっとした日本語」と戦う](https://zenn.dev/knowledgesense/articles/83c89503b6531b)

### 2.4 Japanese Embedding Models

| Model | Developer | Key Feature |
|-------|-----------|-------------|
| **intfloat/multilingual-e5-large** | Microsoft | Strong multilingual including Japanese |
| **cl-nagoya/sup-simcse-ja-large** | Nagoya University | Japanese-specific SimCSE |
| **pkshatech/GLuCoSE-base-ja** | PKSHA | Japanese document embedding |
| **bclavie/JaColBERT** | Benjamin Clavie | Japanese ColBERT for dense retrieval |
| **Ruri** | Tokyo University | Japanese-specific (2024) |

**Source:** [RAG における埋め込みモデルの比較](https://note.com/alexweberk/n/ncccfdab3f4bb)

### 2.5 Japanese LLM Models for RAG

| Model | Developer | Key Feature |
|-------|-----------|-------------|
| **Llama-3-ELYZA-JP** | ELYZA (東大松尾研) | Claims to exceed GPT-4 for Japanese |
| **Llama3-8B-Swallow** | Tokyo Institute of Technology | Enhanced Japanese capability |
| **youri-7b** | rinna | Production-ready Japanese |
| **japanese-gpt-neox-3.6b** | rinna | 312.5B tokens training |

### 2.6 Japanese Hybrid Search Implementation

**Key Finding:** Simple combination of vector + keyword may not improve performance. Proper tuning is essential.

**Recommended Stack:**
- Embedding: Ruri (Japanese-specific, 2024)
- Vector Search: Voyager (approximate nearest neighbor)
- Keyword Search: BM25 with MeCab tokenization
- Integration: LangChain BM25Retriever with custom tokenizer

**Source:** [ハイブリッド検索で必ずしも検索性能が上がるわけではない](https://hironsan.hatenablog.com/entry/improving-performance-of-hybrid-search)

### 2.7 Japanese RAG Open Source Projects

| Project | Description | Link |
|---------|-------------|------|
| **JP RAG SAMPLE** | AWS RAG sample for Japanese | [aws-samples/jp-rag-sample](https://github.com/aws-samples/jp-rag-sample) |
| **JQaRA** | Japanese Q&A dataset for RAG evaluation | [hotchpotch/JQaRA](https://github.com/hotchpotch/JQaRA) |
| **kotaemon** | Open source RAG UI (Japanese support) | [Cinnamon/kotaemon](https://github.com/Cinnamon/kotaemon) |

---

## Part 3: Korean RAG Innovations (한국어 연구)

### 3.1 AutoRAG - Automated RAG Optimization

**Developer:** Marker-Inc-Korea

**Key Features:**
- AutoML-style automatic module evaluation
- Finds optimal pipeline for your specific data
- Single YAML file deployment
- Korean language package available

```bash
pip install "AutoRAG[ko]"
```

**Source:** [AutoRAG GitHub](https://github.com/marker-inc-korea/autorag)

### 3.2 Kakao Enterprise Chunking Innovation (if kakaoAI 2024)

**Key Insight:** "Chunk = maximum unit that can bundle minimum homogeneous meaning"

**Best Practices:**
1. Split documents at sentence level (not all at once)
2. Focus strongly on single topic per chunk
3. High-quality chunks improve search quality dramatically

**KANANA Model Performance:**
- RAG performance: 92% of GPT-4o
- Function calling: 92% of GPT-4o
- Summarization: 106% of GPT-4o

**Source:** [if카카오2024 카카오엔터프라이즈의 RAG](https://byline.network/2024/10/241022_kakaorag_3/)

### 3.3 Korean Embedding Models

| Model | Developer | Performance |
|-------|-----------|-------------|
| **BGE-M3** | BAAI | Best overall for Korean RAG |
| **Solar Embedding-1-Large** | Upstage | +7.84 points vs previous version |
| **KURE-v1** | KAIST (nlpai-lab) | Best for conversational/emotional text |
| **KoSimCSE-RoBERTa-multitask** | Korean NLP Lab | Highest AVG score for Korean |

**Source:** [Solar Embedding Performance](https://www.upstage.ai/blog/en/solar-embedding-1-large)

### 3.4 Korean Reranking Strategy

**Key Finding:** RAG accuracy depends more on document ORDER than mere presence in context.

**Two-Stage Retrieval:**
1. Stage 1: Vector search for initial candidate retrieval
2. Stage 2: Reranker-based relevance re-scoring

**Source:** [한국어 Reranker를 활용한 검색 증강 생성(RAG) 성능 올리기](https://aws.amazon.com/ko/blogs/tech/korean-reranker-rag/)

### 3.5 Naver Cloud RAG Platform

**Features:**
- RESTful API for question answering
- Document management (upload, query, delete)
- HyperCLOVA X integration
- Multimodal RAG support (images + text)

**Vector DB Options:**
- PostgreSQL with pgvector
- Naver Search Engine Service
- Custom server deployments

**Source:** [RAG 개요 - Naver Cloud](https://api.ncloud-docs.com/docs/rag-overview)

### 3.6 Corrective RAG (Korean Innovation)

**Architecture:**
- Self-corrects retrieval results
- Evaluates document relevance and reliability (not just similarity)
- Improves utilization of augmented documents

**Source:** [검색증강생성(RAG)의 한계점과 보완책](https://blog-ko.superb-ai.com/limitations-and-workarounds-for-rag/)

### 3.7 Korean RAG Open Source Projects

| Project | Description | Link |
|---------|-------------|------|
| **Korean-Embedding-Model-Performance-Benchmark** | RAG retriever benchmark | [ssisOneTeam](https://github.com/ssisOneTeam/Korean-Embedding-Model-Performance-Benchmark-for-Retriever) |
| **langchain-kr** | LangChain Korean tutorial | [teddylee777/langchain-kr](https://github.com/teddylee777/langchain-kr) |
| **KoAlpaca** | Korean Alpaca (Polyglot-ko 5.8B) | [Beomi/KoAlpaca](https://github.com/Beomi/KoAlpaca) |

---

## Part 4: German RAG Innovations (Deutsche Forschung)

### 4.1 Fraunhofer Research Breakthroughs

| Institute | Innovation | Impact |
|-----------|------------|--------|
| **Fraunhofer IESE** | Dependable AI RAG frameworks | Reduced hallucinations |
| **Fraunhofer IAIS** | RAG-Ex explanation framework | Model-agnostic explainability |
| **Fraunhofer Austria** | **Knowledge Graph + RAG hybrid** | Significantly reduced hallucinations |
| **Fraunhofer IPA** | Need-to-know principle for GDPR | Privacy compliance |

**Key Innovation (Fraunhofer Austria):**
Combines semantic vector search with symbolic graph reasoning. Results in more explainable and contextually aware outputs with dramatically reduced hallucinations.

**Source:** [Fraunhofer Austria Knowledge Graph RAG](https://futurezone.at/science/fraunhofer-austria-licht-black-box-kuenstliche-intelligenz-ki-rag-wissensgraph-bibliothek/403102335)

### 4.2 Deutsche Telekom Production Systems

**LMOS Platform:**
- Uses **Qdrant** vector database (Rust-based, high-performance)
- **Wurzel** - open-source Python ETL framework for RAG
- Multitenancy, job scheduling, standardized workflows
- **Production proof:** FTTH chatbot with 400 documents (900 pages each)

**T-Systems AI Foundation Services:**
- Production RAG API with **50+ retrieval settings**
- Supports multiple formats: docx, pdf, xlsx, diagrams
- Vector database in customer's private cloud (data sovereignty)

**Source:** [Deutsche Telekom AI Agents at Scale](https://www.infoworld.com/article/4018349/how-deutsche-telekom-designed-ai-agents-for-scale.html)

### 4.3 German Privacy & Data Sovereignty

**Core Principles:**
- GDPR compliance from day one (not retrofitted)
- Local LLM deployment preferred
- **Datensouveränität** (data sovereignty) as primary concern
- Legal clarity around data usage

**Ger-RAG-eval Dataset:**
- Public benchmark for German RAG evaluation
- Based on German Wikipedia data
- Available on Hugging Face: [deutsche-telekom/Ger-RAG-eval](https://huggingface.co/datasets/deutsche-telekom/Ger-RAG-eval)

---

## Part 5: French RAG Innovations (Recherche Française)

### 5.1 Mistral AI Efficiency Optimizations

**Chunk Size Strategy:**
- Smaller chunks = better retrieval (less filler text obscuring semantics)
- Custom chunk sizes per document type
- **AST parser** for code chunks

**RAG Triad Evaluation Framework:**
1. **Context Relevance:** Were retrieved documents actually relevant?
2. **Groundedness:** Is response grounded in retrieved context?
3. **Answer Relevance:** Does answer address the original question?

**Source:** [Mistral RAG Quickstart](https://docs.mistral.ai/guides/rag/)

### 5.2 Mistral Embedding Models

| Model | Dimensions | Context | MTEB Score |
|-------|------------|---------|------------|
| **mistral-embed** | 1024 | 8,000 tokens | 55.26 |
| **codestral-embed** | up to 3072 | - | State-of-art for code |

**Key Insight:** Higher dimensions = better semantic capture BUT more resources. Mistral allows dimension reduction for speed.

**Source:** [Mistral Text Embeddings](https://docs.mistral.ai/capabilities/embeddings/text_embeddings)

### 5.3 Super RAGs Research (Breakthrough)

**Novel approach** tested on Mistral 8x7B v1:
- Integrates external knowledge with minimal structural modifications

**Performance Gains:**
- Accuracy: 85.5% → **92.3%** (+6.8%)
- Query speed: 78ms → **65ms** (-17% latency)

**Key Finding:** Architectural optimization matters more than model size.

**Source:** [Super RAGs Paper](https://arxiv.org/html/2404.08940v1)

### 5.4 French Government RAG Guide (November 2024)

**Official guide from Direction générale des Entreprises:**
- First official AI guide for French businesses
- Covers: use cases, prerequisites, costs, best practices

**Recommended Use Cases:**
- General business assistant (meeting minutes)
- Legal compliance verification
- HR assistant
- Technical documentation research
- Sales assistant

**Source:** [French Government RAG Guide](https://www.entreprises.gouv.fr/files/files/Publications/2024/Guides/20241127-bro-guide-ragv4-interactif.pdf)

### 5.5 French Vector Database Recommendations

**Top recommendations:**
1. **Weaviate** - Native LLM integration, semantic search
2. **Milvus** - Large-scale, HNSW/IVF indexes, horizontal scalability
3. **Qdrant** - High performance, low latency (Deutsche Telekom choice)
4. **Chroma DB** - Open-source, SQLite-based, fast prototyping
5. **Pinecone** - Fully managed (if cloud acceptable)

**For local deployment:** Qdrant or Milvus (open-source, production-proven)

---

## Part 6: Russian RAG Innovations (Российские исследования)

### 6.1 Three-Phase RAG Optimization

| Phase | Timeline | Accuracy | Focus |
|-------|----------|----------|-------|
| **Basic RAG** | 2-4 weeks | 60-70% | Simple chunking, basic vector search |
| **Hybrid + Metadata** | +2-3 weeks | +15-25% | Keyword + semantic, metadata filtering |
| **Reranking + Context** | Production | 85-90% | Cross-encoder, context enhancement |

### 6.2 Adaptive RAG (Critical Innovation)

**Dynamic query complexity classification:**
- **Simple queries:** No retrieval needed (direct LLM)
- **Moderate queries:** Single-step retrieval
- **Complex queries:** Multi-step retrieval with reasoning

**Benefits:**
- Reduces latency (skip retrieval when unnecessary)
- Reduces costs (fewer vector searches)
- Better UX (fast responses for simple questions)

### 6.3 Corrective RAG (CRAG)

**Enhancement over traditional RAG:**
- **Retrieval evaluator** filters/rejects irrelevant documents
- **Web search augmentation** when local context insufficient

**Flow:**
```
Query → Initial Retrieval → Relevance Evaluation →
  → [Relevant] → Generate
  → [Irrelevant] → Web Search → Generate
  → [Partial] → Refine + Web Search → Generate
```

### 6.4 Yandex Solutions

**Yandex DataSphere advanced_rag repository:**
1. **simple_rag:** Naive RAG + synthetic question-based search
2. **graph_rag:** Knowledge graph extraction (Microsoft-inspired)
3. **multiagent:** Multi-agent RAG with Prolog logical inference

**Source:** [Yandex DataSphere advanced_rag](https://github.com/yandex-datasphere/advanced_rag)

### 6.5 Sber AI Solutions

**Giga-Embeddings (Open-Source):**
- Best in class on ruMTEB benchmark
- High speed, accuracy, adaptability
- Can be fine-tuned for specific domains
- **Open license** for commercial use

**GigaChat:**
- Russian ChatGPT alternative
- 2.5M+ users
- Multimodal: text, images, code
- RAG-compatible

### 6.6 Russian Vector Database Recommendations

**PostgreSQL + vector extension:**
- Ideal when PostgreSQL is primary DB
- Sufficient for ~100k documents
- No need for separate DB

**Redis (v7+) with Redis Search:**
- HNSW index support
- Fast vector caching
- Small datasets (<10M vectors)
- **Extremely low latency**

---

## Part 7: Quantized LLM RAG Optimizations

### 7.1 Quantization Impact on RAG Quality

| Quantization | Quality Impact | Speed Gain | Use Case |
|--------------|----------------|------------|----------|
| **Q8 (8-bit)** | Minimal loss | 1.5-2x | Production |
| **Q4 (4-bit)** | 2-5% accuracy drop | 2-3x | Resource-constrained |
| **Q2 (2-bit)** | Noticeable drop | 3-4x | Fast tier only |

### 7.2 Quantized Embedding Options

- **ONNX quantization** of sentence-transformers
- **int8 embedding** for 2x memory reduction
- **Mixed precision** (fp16 compute, int8 storage)

### 7.3 llama.cpp RAG Best Practices

- Use `--mmap` for faster loading
- Set appropriate `--ctx-size` for RAG context
- Use `--batch-size` for parallel embedding generation
- Enable Metal acceleration on macOS

---

## Part 8: Metal/Apple Silicon Optimizations

### 8.1 MLX Framework for RAG

**Apple's MLX** is optimized for Apple Silicon:
- Unified memory = no CPU↔GPU transfer overhead
- Native Metal acceleration
- Growing model ecosystem

### 8.2 FAISS on Apple Silicon

**Current Limitations:**
- No native Metal support for FAISS
- Uses CPU SIMD instructions

**Alternatives:**
- **Qdrant** (Rust-based, excellent macOS performance)
- **USearch** (Apple Silicon optimized)
- **Voyager** (Python, good Apple Silicon support)

### 8.3 llama.cpp Metal Settings

```bash
./server \
  --model model.gguf \
  --n-gpu-layers 99 \
  --flash-attn \
  --ctx-size 8192 \
  --batch-size 512
```

**Key:** Use `--n-gpu-layers 99` to offload all layers to Metal.

---

## Part 9: European Privacy-Preserving RAG

### 9.1 GDPR-Compliant Architectures

**Three Privacy Paradigms:**

1. **Data Localization:**
   - Process sensitive info locally/at edge
   - On-device anonymization
   - Local LLM deployment

2. **Collaborative Learning:**
   - Federated learning approaches
   - Multi-institutional cooperation without data sharing

3. **Secure Access Control:**
   - Authentication, authorization, audit
   - Throughout entire RAG pipeline

### 9.2 Advanced Privacy Techniques

**Federated Learning:**
- European bank consortium example
- 95% accuracy of centralized model
- Full GDPR compliance

**Differential Privacy:**
- 97% reduction in unintended information exposure
- 92% performance maintained

**Homomorphic Encryption:**
- Computation on encrypted embeddings
- Privacy-preserving federated embedding learning

**Confidential Computing:**
- Hardware-based Trusted Execution Environment (TEE)
- Can secure entire RAG inference process

---

## Part 10: CJK-Specific Optimizations

### 10.1 Tokenization Challenges

CJK languages require fundamentally different tokenization:
- **Japanese:** No word boundaries (morphological analysis required)
- **Korean:** Agglutinative morphology with mixed scripts
- **Chinese:** No spaces, character-level or word-level options

**UTF-8 Impact:** CJK characters require 3 bytes vs 1 byte for English, affecting context window utilization.

### 10.2 Best Embedding Models for CJK

1. **BGE-M3:** Best overall for CJK, handles multiple granularities
2. **intfloat/multilingual-e5-large:** Strong Japanese performance
3. **Upstage Solar Embedding:** Optimized for Korean, Japanese, English

### 10.3 Chunk Overlap Recommendations

- **Overlap:** 10-25% of chunk size
- **Rationale:** CJK sentences may split mid-concept
- **Tokenizer alignment:** Match chunk boundaries with tokenizer behavior

---

## Summary: Key Innovations by Region

| Region | Top Innovation | Implementation Priority |
|--------|---------------|------------------------|
| **China** | Two-Stage Reranking | HIGH - +15-25% accuracy |
| **Japan** | Morphological Chunking | MEDIUM - CJK handling |
| **Korea** | AutoRAG Optimization | MEDIUM - Automated tuning |
| **Germany** | Knowledge Graph RAG | HIGH - Reduced hallucinations |
| **France** | RAG Triad Evaluation | MEDIUM - Quality monitoring |
| **Russia** | Adaptive Routing | HIGH - 30-40% cost reduction |

---

## Key Research Sources

### Chinese
- [20多种RAG优化方法](https://zhuanlan.zhihu.com/p/708312114)
- [GraphRAG中文文档](https://www.graphrag.club/)
- [一文读懂RAG](https://zhuanlan.zhihu.com/p/675509396)

### Japanese
- [RAG入門: 精度改善の手法28選](https://qiita.com/FukuharaYohei/items/0949aaac17f7b0a4c807)
- [ハイブリッド検索の実装](https://qiita.com/Shakshi3104/items/6ca3882ba45a4924bf0d)
- [NVIDIA日本語リランキング](https://developer.nvidia.com/ja-jp/blog/rag-with-sota-reranking-model-in-japanese/)

### Korean
- [AutoRAG GitHub](https://github.com/marker-inc-korea/autorag)
- [Korean Reranker AWS Blog](https://aws.amazon.com/ko/blogs/tech/korean-reranker-rag/)
- [if카카오2024 RAG](https://byline.network/2024/10/241022_kakaorag_3/)

### German
- [Fraunhofer KG-RAG](https://futurezone.at/science/fraunhofer-austria-licht-black-box-kuenstliche-intelligenz-ki-rag-wissensgraph-bibliothek/403102335)
- [Deutsche Telekom AI Agents](https://www.infoworld.com/article/4018349/how-deutsche-telekom-designed-ai-agents-for-scale.html)

### French
- [Mistral RAG Guide](https://docs.mistral.ai/guides/rag/)
- [Super RAGs Paper](https://arxiv.org/html/2404.08940v1)
- [French Government RAG Guide](https://www.entreprises.gouv.fr/files/files/Publications/2024/Guides/20241127-bro-guide-ragv4-interactif.pdf)

### Russian
- [Yandex advanced_rag](https://github.com/yandex-datasphere/advanced_rag)
- [Russian RAG Techniques](https://teletype.in/@abletobetable/rag_techniques)

### Privacy & Compliance
- [Privacy Challenges in RAG](https://arxiv.org/html/2511.11347)
- [Privacy-Preserving RAG](https://www.ijfmr.com/papers/2024/6/30421.pdf)

---

## Related Documentation

- [CGRAG Enhancement Implementation Plan](./CGRAG_ENHANCEMENT_PLAN.md)
- [SESSION_NOTES.md](../../SESSION_NOTES.md)
