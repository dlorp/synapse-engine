# Context Window Allocation Viewer - Visual Examples

## Component States

### 1. Empty State (No Query Data)
```
╔═══════════════════════════════════════════════════════════════════════╗
║ ─ CONTEXT WINDOW ALLOCATION ──────────────────────────────────────── ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║                        NO ALLOCATION DATA                             ║
║                   Submit a query to see token allocation              ║
║                          (gray, opacity 60%)                          ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### 2. Loading State
```
╔═══════════════════════════════════════════════════════════════════════╗
║ ─ CONTEXT WINDOW ALLOCATION ──────────────────────────────────────── ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║                      LOADING ALLOCATION...                            ║
║                    (cyan, pulsing 1.5s cycle)                         ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### 3. Low Utilization (45% - Green)
```
╔═══════════════════════════════════════════════════════════════════════╗
║ ─ CONTEXT WINDOW ALLOCATION ──────────────────────────────────────── ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  SYSTEM PROMPT      [■■■] 450 tokens (5.5%)                          ║
║  CGRAG CONTEXT      [■■■■■■■■■■■■] 3000 tokens (36.6%)               ║
║  USER QUERY         [■] 250 tokens (3.1%)                             ║
║  RESPONSE BUDGET    [─────────] 0 tokens (0.0%)                       ║
║                                                                       ║
║  ───────────────────────────────────────────────────────────────────  ║
║                                                                       ║
║  TOTAL: 8192 tokens | USED: 3700 (45.2%) | REMAINING: 4492           ║
║                          (green #00ff41)                              ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### 4. Medium Utilization (67% - Orange)
```
╔═══════════════════════════════════════════════════════════════════════╗
║ ─ CONTEXT WINDOW ALLOCATION ──────────────────────────────────────── ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  SYSTEM PROMPT      [■■■] 450 tokens (5.5%)                          ║
║  CGRAG CONTEXT      [■■■■■■■■■■■■■■■■■] 4500 tokens (54.9%)          ║
║  USER QUERY         [■] 300 tokens (3.7%)                             ║
║  RESPONSE BUDGET    [■] 250 tokens (3.1%)                             ║
║                                                                       ║
║  ───────────────────────────────────────────────────────────────────  ║
║                                                                       ║
║  TOTAL: 8192 tokens | USED: 5500 (67.1%) | REMAINING: 2692           ║
║                         (orange #ff9500)                              ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### 5. High Utilization (87% - Red with Warning)
```
╔═══════════════════════════════════════════════════════════════════════╗
║ ─ CONTEXT WINDOW ALLOCATION ──────────────────────────────────────── ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  SYSTEM PROMPT      [■■■] 450 tokens (5.5%)                          ║
║  CGRAG CONTEXT      [■■■■■■■■■■■■■■■■■■■■■■■■■■] 6000 tokens (73.2%) ║
║  USER QUERY         [■■] 250 tokens (3.1%)                            ║
║  RESPONSE BUDGET    [■■■■■] 1492 tokens (18.2%)                       ║
║                                                                       ║
║  ───────────────────────────────────────────────────────────────────  ║
║                                                                       ║
║  TOTAL: 8192 tokens | USED: 7200 (87.9%) | REMAINING: 992            ║
║                          (red #ff0000, blinking)                      ║
║                                                                       ║
║  ╔═════════════════════════════════════════════════════════════════╗ ║
║  ║ ⚠ Warning: Context window >80% utilized                        ║ ║
║  ║            (orange border, pulsing glow 2s cycle)               ║ ║
║  ╚═════════════════════════════════════════════════════════════════╝ ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### 6. High Utilization with Expanded CGRAG Artifacts
```
╔═══════════════════════════════════════════════════════════════════════╗
║ ─ CONTEXT WINDOW ALLOCATION ──────────────────────────────────────── ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  SYSTEM PROMPT      [■■■] 450 tokens (5.5%)                          ║
║  CGRAG CONTEXT      [■■■■■■■■■■■■■■■■■■■■■■■■■■] 6000 tokens (73.2%) ║
║  USER QUERY         [■■] 250 tokens (3.1%)                            ║
║  RESPONSE BUDGET    [■■■■■] 1492 tokens (18.2%)                       ║
║                                                                       ║
║  ───────────────────────────────────────────────────────────────────  ║
║                                                                       ║
║  TOTAL: 8192 tokens | USED: 7200 (87.9%) | REMAINING: 992            ║
║                          (red #ff0000, blinking)                      ║
║                                                                       ║
║  ╔═════════════════════════════════════════════════════════════════╗ ║
║  ║ ⚠ Warning: Context window >80% utilized                        ║ ║
║  ╚═════════════════════════════════════════════════════════════════╝ ║
║                                                                       ║
║  ╔═════════════════════════════════════════════════════════════════╗ ║
║  ║ ▼ CGRAG ARTIFACTS (5)                    (cyan, bold)          ║ ║
║  ╠═════════════════════════════════════════════════════════════════╣ ║
║  ║                                                                 ║ ║
║  ║ │ #1  docs/api-reference.md       1200 tokens  Relevance: 95.2%║ ║
║  ║ │     Complete REST API documentation including authentication, ║ ║
║  ║ │     endpoints, request/response schemas, and error codes...   ║ ║
║  ║ │     (hover: border glows, background lightens)                ║ ║
║  ║ │                                                                ║ ║
║  ║ │ #2  docs/architecture.md        950 tokens   Relevance: 92.8% ║ ║
║  ║ │     System architecture overview with component diagrams,     ║ ║
║  ║ │     data flow, and integration patterns for CGRAG system...   ║ ║
║  ║ │                                                                ║ ║
║  ║ │ #3  docs/cgrag-guide.md         850 tokens   Relevance: 90.1% ║ ║
║  ║ │     CGRAG implementation guide covering vector embeddings,    ║ ║
║  ║ │     FAISS indexing, and retrieval optimization strategies...  ║ ║
║  ║ │                                                                ║ ║
║  ║ │ #4  docs/query-routing.md       750 tokens   Relevance: 88.5% ║ ║
║  ║ │     Query complexity assessment and model tier selection      ║ ║
║  ║ │     algorithms with performance benchmarks and tuning...      ║ ║
║  ║ │                                                                ║ ║
║  ║ │ #5  docs/deployment.md          650 tokens   Relevance: 85.3% ║ ║
║  ║ │     Docker deployment guide including compose configuration,  ║ ║
║  ║ │     environment variables, and production best practices...   ║ ║
║  ║ │                                                                ║ ║
║  ║                 (scrollable, custom phosphor scrollbar)         ║ ║
║  ╚═════════════════════════════════════════════════════════════════╝ ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

## Hover/Interaction States

### Budget Row Hover
```
║  CGRAG CONTEXT      [■■■■■■■■■■■■■■■■■■■■] 6000 tokens (73.2%)      ║
                      ↑
            (background: rgba(255, 149, 0, 0.05))
            (padding: 4px applied on hover)
```

### CGRAG Artifact Hover
```
║ │ #1  docs/api-reference.md       1200 tokens  Relevance: 95.2%      ║
║ │     Complete REST API documentation including authentication...    ║
      ↑
  (border-left: 4px solid #ff9500)
  (background: rgba(255, 149, 0, 0.1))
  (smooth transition 200ms)
```

### Details Summary Hover
```
║ ▼ CGRAR ARTIFACTS (5)                    (cyan, bold)                ║
    ↑
(background: rgba(0, 255, 255, 0.1))
(text-shadow: 0 0 5px cyan)
(cursor: pointer)
```

## Responsive Breakpoints

### Desktop (>1024px)
```
Full 3-column layout:
[LABEL     ] [BAR                    ] [COUNT       ]
CGRAG CONTEXT [■■■■■■■■■■■■■■■■■■■■] 6000 tokens (73%)
```

### Tablet (768-1024px)
```
Reduced spacing, slightly smaller fonts:
[LABEL   ] [BAR              ] [COUNT    ]
CGRAG      [■■■■■■■■■■■■■■■■] 6000 (73%)
```

### Mobile (<768px)
```
Stacked vertical layout:
CGRAG CONTEXT
[■■■■■■■■■■■■■■■■■■■■]
6000 tokens (73%)

(each component on separate lines)
```

### Small Mobile (<480px)
```
Compact fonts (10px):
CGRAG CONTEXT
[■■■■■■■■■■]
6000 (73%)
```

## Color Reference

**Primary Colors:**
- Phosphor Orange: `#ff9500` (primary text, bars)
- Cyan: `#00ffff` (accent, labels)
- Pure Black: `#000000` (background)

**Utilization Colors:**
- Low (<60%): `#00ff41` (green)
- Medium (60-80%): `#ff9500` (orange)
- High (>80%): `#ff0000` (red)

**State Colors:**
- Processing: `#00ffff` (cyan, pulsing)
- Error: `#ff0000` (red)
- Success: `#00ff41` (green)

**Opacity Levels:**
- Empty state: 60%
- Separator: 50%
- Hover background: 5-10%
- Border glow: 10-30%

## Animation Timings

**Pulse (Loading):** 1.5s ease-in-out infinite
**Blink (High Utilization):** 1s infinite
**Warning Pulse:** 2s ease-in-out infinite
**Fade In (Details):** 0.3s ease-out
**Hover Transitions:** 200ms ease

## Typography

**Fonts:**
- Primary: JetBrains Mono (monospace)
- Fallback: IBM Plex Mono, monospace

**Sizes:**
- Component labels: 13px (desktop), 12px (tablet), 11px (mobile)
- Token counts: 13px with `font-variant-numeric: tabular-nums`
- Summary: 12px (small)
- Artifact preview: 11px
- Headers: 12px bold

**Effects:**
- Letter spacing: 0.05em (labels)
- Text shadow: 0 0 3-5px (glows)
- Line height: 1.8 (bars), 1.5 (previews)

