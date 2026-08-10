# AskDB

Natural language to SQL, powered by schema intelligence and semantic retrieval. A layered architecture where production and experimental retrieval systems coexist.

## Overview

AskDB transforms natural language questions into SQL queries and executes them against a SQLite database. The system combines deterministic schema-based retrieval with emerging semantic retrieval capabilities, all while maintaining stability in the production pipeline.

**Key architectural insight:** The system is layered, not rewritten. The core AskDB pipeline remains stable while schema intelligence gets richer and semantic retrieval improves in parallel—no production integration yet.

## Architecture

### Layer 1: Data & Schema Foundation

The source of truth for the database structure.

- **`schema.sql`** — SQLite schema definition
- **`create_db.py`** — Database initialization
- **`schema_extractor.py`** — SQLAlchemy-based introspection. Extracts tables, columns, types, primary keys, foreign keys, and sample values

### Layer 2: Retrieval Systems (Dual Path)

Two independent retrieval paths run in parallel.

#### Path A: Legacy Schema Documents (Production)

Table-level document retrieval designed for stability and broad coverage.

- **`schema_documents.py`** — Converts raw schema into four table-level documents (customers, products, orders, order_items)
- Status: **Production** — actively used
- Constraint: Works with broad categories, not fine-grained concepts

#### Path B: Chunk-Based Semantic Retrieval (Experimental)

Structured semantic chunks for granular schema understanding. Independent from production pipeline.

- **`schema_chunks.py`** — Creates semantic chunks (e.g., `customers.customer_location`, `products.product_pricing`, `orders.order_status`)
- **`vector_store.py`** — Local vector index using `sentence-transformers/all-MiniLM-L6-v2`. Normalized embeddings with cosine/dot-product similarity
- **`chunk_embeddings.npy`** — Persisted embedding vectors
- **`chunk_metadata.json`** — Chunk metadata and content
- **`retrieve_vector_schema(question, top_k, min_score)`** — Retrieval contract
- Status: **Experimental** — isolated, tested locally, ready for adoption when ranking improves
- API: Returns chunk objects with id, table, topic, content, and similarity score

### Layer 3: Query Processing

Deterministic SQL generation with repair and validation.

- **`text_to_sql.py`** — Gemini-based NL-to-SQL generation
- **`sql_repair.py`** — Automated error recovery
- **`sql_validator.py`** — Syntax and semantic validation
- **`database_executor.py`** — Safe, read-only SQL execution
- **`result_explainer.py`** — Natural language explanation of results

### Layer 4: Orchestration & API

Coordinates the full pipeline and exposes endpoints.

- **`query_engine.py`** — Main orchestrator. Flow: generate SQL → execute → repair on failure → explain results
- **`api.py`** — FastAPI server with endpoints:
  - `GET /health` — Health check
  - `POST /ask` — Natural language query submission
- **`App.tsx`** — React frontend for user interaction

### Layer 5: Evaluation

Semantic correctness testing for the NL-to-SQL pipeline.

- **`evaluate.py`** — Test runner
- **`test_queries.json`** — Test cases with expected SQL and results
- **`evaluation_results.json`** — Test results and metrics

## Design Philosophy

### Dual-Path Strategy

The architectural choice to maintain two retrieval systems in parallel enables:

- **Production stability** — The legacy path continues to serve requests reliably
- **Safe experimentation** — The chunk-based retriever is isolated and tested locally
- **Easy A/B testing** — Compare retrieval quality without shipping breaking changes
- **Low risk upgrade path** — Adopt the new retriever when ranking demonstrably improves

### No Production Integration Yet

The experimental chunk-based system is intentionally disconnected from the main SQL generation engine. This isolation protects the production pipeline while allowing the retrieval layer to mature independently.

## File Structure

```
askdb/
├── schema/
│   ├── schema.sql
│   ├── create_db.py
│   └── schema_extractor.py
├── retrieval/
│   ├── schema_documents.py      (production path)
│   ├── schema_chunks.py         (experimental path)
│   ├── vector_store.py          (experimental path)
│   ├── chunk_embeddings.npy     (experimental path)
│   └── chunk_metadata.json      (experimental path)
├── query/
│   ├── text_to_sql.py
│   ├── sql_repair.py
│   ├── sql_validator.py
│   ├── database_executor.py
│   └── result_explainer.py
├── orchestration/
│   ├── query_engine.py
│   └── api.py
├── frontend/
│   └── App.tsx
├── evaluation/
│   ├── evaluate.py
│   ├── test_queries.json
│   └── evaluation_results.json
└── README.md
```

## Data Flow

### Production Flow (Legacy Retrieval)

```
User Question
    ↓
[Schema Extraction] → Schema documents (table-level)
    ↓
[Retrieval] → Relevant tables
    ↓
[SQL Generation] (Gemini)
    ↓
[Validation] → Pass/Fail
    ↓
[Repair] (if needed)
    ↓
[Execution] (read-only)
    ↓
[Explanation] (NL result)
    ↓
Response
```

### Experimental Flow (Chunk-Based Retrieval)

```
User Question
    ↓
[Vector Embedding] (all-MiniLM-L6-v2)
    ↓
[Similarity Search] → Top-K chunks
    ↓
[Filtering] (min_score threshold)
    ↓
Response (id, table, topic, content, score)
    ↓
[Ready for integration when ranking improves]
```

## Key Contracts

### `retrieve_vector_schema(question, top_k=5, min_score=0.3)`

Returns list of chunk objects:

```python
{
    "id": "string",
    "table": "customers",
    "topic": "customer_location",
    "content": "string (full description)",
    "score": 0.87
}
```

## Getting Started

### Setup

1. **Create the database**
   ```bash
   python create_db.py
   ```

2. **Extract schema**
   ```bash
   python schema_extractor.py
   ```

3. **Build retrieval indices**
   ```bash
   # Production path (automatic)
   python schema_documents.py
   
   # Experimental path (optional)
   python schema_chunks.py
   python vector_store.py  # Builds embeddings
   ```

4. **Start the API**
   ```bash
   python api.py
   ```
   Server runs on `http://localhost:8000`

5. **Test a query**
   ```bash
   curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "How many orders were placed in the last 30 days?"}'
   ```

### Evaluate

Run semantic correctness tests:

```bash
python evaluate.py
```

Results written to `evaluation_results.json`.

## When to Use Experimental Retrieval

The chunk-based retriever is ideal for testing when:

- Fine-grained schema knowledge improves query quality
- Column-level context matters more than table-level overviews
- Ranking improvements can be measured via A/B tests on `test_queries.json`

To integrate into production:

1. Run `test_queries.json` against both retrievers
2. Compare `evaluation_results.json` metrics
3. If experimental path wins on semantic accuracy, wire it into `query_engine.py`
4. Ship the integrated version behind a feature flag initially

## Technologies

- **Database:** SQLite with SQLAlchemy
- **NL-to-SQL:** Google Gemini API
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`
- **API:** FastAPI
- **Frontend:** React (TypeScript)

## Performance Considerations

- **Legacy retrieval:** O(1) lookup via table documents, no latency penalty
- **Chunk-based retrieval:** O(n) similarity search, typically <50ms for 100–200 chunks
- **SQL generation:** Depends on Gemini API latency (typically 1–3s)
- **Execution:** Database-dependent; evaluated on `test_queries.json`

## Next Steps

### Short Term

- Improve chunk-based retrieval ranking via prompt engineering
- A/B test on production dataset
- Measure quality improvements on `test_queries.json`

### Long Term

- Integrate top-performing retriever into production pipeline
- Add support for multi-table joins in chunk context
- Expand chunk taxonomy for domain-specific schemas

## Contributing

When adding schema changes:

1. Update `schema.sql`
2. Re-run `schema_extractor.py`
3. Regenerate both retrieval indices
4. Update `test_queries.json` with new test cases
5. Run `evaluate.py` to confirm no regressions

