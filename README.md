# 🚀 AskDB

> **Natural Language to SQL Query Engine with Dual Retrieval Intelligence**

[![Status](https://img.shields.io/badge/status-production-blue.svg)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

AskDB is a schema-aware natural-language-to-SQL system that converts user questions into validated, read-only SQL queries. It combines deterministic table-level schema retrieval (production) with an experimental semantic chunk-based retrieval layer to improve query understanding.

**The core innovation:** Building a precise bridge between human language → database schema → safe SQL execution.

---

## 📋 Table of Contents

- [What is AskDB?](#-what-is-askdb)
- [System Architecture](#-system-architecture)
- [Production vs Experimental](#-production-vs-experimental-paths)
- [Deep Dive by Layer](#-deep-dive-by-layer)
- [How It Works (End-to-End)](#-how-it-works-end-to-end)
- [Key Technical Insights](#-key-technical-insights)
- [Getting Started](#-getting-started)
- [API Reference](#-api-reference)
- [Evaluation & Improvements](#-evaluation--improvements)
- [File Responsibility Chart](#-file-responsibility-chart)

---

## ✨ What is AskDB?

At its core, AskDB does one thing:

```
User asks a question in plain English
        ↓
AskDB converts it to SQL
        ↓
Executes the SQL safely
        ↓
Explains the result in plain English
```

**Example:**

```
User: "Which customers placed the most orders?"

AskDB:
1. Understands the question structure
2. Looks up the database schema (customers, orders tables)
3. Generates SQL: SELECT c.id, COUNT(o.id) FROM customers c 
                  JOIN orders o ON c.id = o.customer_id 
                  GROUP BY c.id ORDER BY COUNT(*) DESC
4. Validates the SQL (read-only, no dangerous operations)
5. Executes it against SQLite
6. Returns: "Customer #42 (Alice Johnson) placed 156 orders, 
            the highest in the database"
```

The user doesn't write SQL. They ask in natural language.

---

## 🏗️ System Architecture

### The Complete Picture

```
                         ┌─────────────┐
                         │    User     │
                         │  Question   │
                         └──────┬──────┘
                                │
                                ▼
                         ┌─────────────┐
                         │ React UI    │
                         │  (App.tsx)  │
                         └──────┬──────┘
                                │
                                ▼
                         ┌─────────────┐
                         │   FastAPI   │
                         │  POST /ask  │
                         └──────┬──────┘
                                │
                                ▼
                      ┌───────────────────┐
                      │   Query Engine    │
                      │ (query_engine.py) │
                      └─────────┬─────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
          🟢 PRODUCTION              🟡 EXPERIMENTAL
                    │                       │
                    ▼                       ▼
           ┌────────────────┐      ┌─────────────────┐
           │ Table-Level    │      │ Chunk Semantic  │
           │ Schema Docs    │      │ Retrieval       │
           │(LEGACY PATH)   │      │(NEW PATH)       │
           └───────┬────────┘      └────────┬────────┘
                   │                        │
                   │                        │
                   │                        ▼
                   │                 Sentence Transformer
                   │                 (all-MiniLM-L6-v2)
                   │                        │
                   │                        ▼
                   │                  Vector Index
                   │                 (normalized dots)
                   │                        │
                   └──────────┬─────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Schema Context  │
                       │ (selected info) │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Gemini LLM     │
                       │  text_to_sql.py │
                       │  NL → SQL       │
                       └────────┬────────┘
                                │
                                ▼
                        Generated SQL
                                │
                                ▼
                       ┌─────────────────┐
                       │  SQL Validator  │
                       │ sql_validator.py│
                       └────────┬────────┘
                                │
                           ┌────┴────┐
                           │         │
                        Valid      Invalid
                           │         │
                           │         ▼
                           │    ┌──────────────┐
                           │    │  SQL Repair  │
                           │    │ sql_repair.py│
                           │    └──────┬───────┘
                           │           │
                           └─────┬─────┘
                                 │
                                 ▼
                       ┌─────────────────┐
                       │  DB Executor    │
                       │ Read-Only SQL   │
                       │database_executor│
                       └────────┬────────┘
                                │
                                ▼
                         SQL Result Rows
                                │
                                ▼
                       ┌─────────────────┐
                       │ Result Explainer│
                       │result_explainer │
                       │ SQL → NL        │
                       └────────┬────────┘
                                │
                                ▼
                        Natural Language
                           Answer
                                │
                                ▼
                       ┌─────────────────┐
                       │   React UI      │
                       │   Displays       │
                       │   Result        │
                       └─────────────────┘
```

### Critical Point

**The vector retriever is NOT currently controlling the main pipeline.**

It's an experimental side path that exists to answer the question:

> Does chunk-level semantic retrieval improve SQL generation quality compared to table-level retrieval?

This is proper experimental design. You keep the production system stable while testing improvements.

---

## 🟢 Production vs 🟡 Experimental Paths

### Production Path (Current, Stable)

The system that actually powers AskDB today:

```
schema.sql
    ↓
create_db.py (creates database)
    ↓
schema_extractor.py (introspects structure)
    ↓
schema_documents.py (table-level documents)
    ↓
text_to_sql.py (Gemini generates SQL)
    ↓
sql_validator.py (checks safety)
    ↓
sql_repair.py (fixes errors)
    ↓
database_executor.py (read-only execution)
    ↓
result_explainer.py (converts to natural language)
    ↓
query_engine.py (orchestrates pipeline)
    ↓
api.py (FastAPI endpoint)
    ↓
App.tsx (React frontend)
```

**Status:** 🟢 Production  
**Tested:** Yes  
**Risk:** Low  
**Powers:** All current queries

### Experimental Path (New, Isolated)

Testing whether fine-grained semantic retrieval works better:

```
schema_extractor.py (same schema info)
    ↓
schema_chunks.py (breaks into semantic chunks)
    ↓
Sentence Transformers (all-MiniLM-L6-v2)
    ↓
vector_store.py (builds local vector index)
    ↓
chunk_embeddings.npy (stores numerical vectors)
    ↓
chunk_metadata.json (stores chunk information)
    ↓
retrieve_vector_schema() (retrieval function)
    ↓
[NOT YET INTEGRATED - Results compared separately]
```

**Status:** 🟡 Experimental  
**Tested:** Isolated evaluation only  
**Risk:** None (doesn't affect production)  
**Purpose:** Compare against legacy for improvement testing

---

## 📚 Deep Dive by Layer

### Layer 1: Database Foundation

#### `schema.sql`

Defines the SQLite database structure. Contains tables like:

```sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT,
    location TEXT,
    registration_date DATE
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE,
    status TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name TEXT,
    category TEXT,
    price REAL
);

CREATE TABLE order_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    unit_price REAL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

**Relationships:**

```
customers
    ↓ customer_id
orders
    ↓ order_id
order_items
    ↓ product_id
products
```

#### `create_db.py`

Instantiates the schema:

```python
def create_database():
    """
    Takes schema.sql
    Creates SQLite database file
    Seeds sample data
    """
    conn = sqlite3.connect('askdb.db')
    conn.executescript(open('schema.sql').read())
    # Seed sample customers, orders, etc.
    conn.commit()
```

When someone clones your project, they can recreate the entire database.

---

### Layer 2: Schema Extraction

#### `schema_extractor.py`

Automatically introspects the database to understand its structure:

```python
def extract_schema():
    """
    Returns structured information about the database:
    
    {
        "tables": ["customers", "products", "orders", "order_items"],
        "columns": {
            "customers": [
                {
                    "name": "customer_id",
                    "type": "INTEGER",
                    "constraints": ["PRIMARY KEY"]
                },
                {
                    "name": "name",
                    "type": "TEXT"
                },
                {
                    "name": "location",
                    "type": "TEXT",
                    "sample_values": ["Silchar", "Guwahati", "Delhi", "Mumbai"]
                }
            ]
        },
        "relationships": {
            "orders.customer_id": "customers.customer_id",
            "order_items.order_id": "orders.order_id",
            "order_items.product_id": "products.product_id"
        }
    }
    """
```

**Why sample values matter:**

The LLM doesn't know your database structure. Telling it:

```
location TEXT
```

is less helpful than:

```
location TEXT
Sample values: Silchar, Guwahati, Delhi, Mumbai
```

Sample values give semantic clues about what the column represents.

---

### Layer 3: Retrieval (Dual Path)

#### 🟢 Path A: `schema_documents.py` (Production)

Converts schema into table-level documents:

```python
def create_schema_documents():
    """
    Creates one document per table
    """
    documents = {
        "customers": """
            Table: customers
            Columns: customer_id (PRIMARY KEY), name, location, registration_date
            Relationships: referenced by orders.customer_id
            Sample data: 1000 customer records
            ...description...
        """,
        "products": """
            Table: products
            Columns: product_id (PRIMARY KEY), name, category, price
            ...
        """,
        "orders": """
            Table: orders
            Columns: order_id (PRIMARY KEY), customer_id (FOREIGN KEY), order_date, status
            Relationships: references customers, referenced by order_items
            ...
        """,
        "order_items": """
            Table: order_items
            Columns: item_id (PRIMARY KEY), order_id (FK), product_id (FK), quantity, unit_price
            Relationships: references orders and products
            ...
        """
    }
    return documents
```

**Flow:**

```
Question: "Which customers placed the most orders?"
    ↓
Retrieval asks: "Which tables are relevant?"
    ↓
Returns: customers, orders (documents)
    ↓
Passes to Gemini as context
    ↓
Gemini knows about these tables and can write SQL
```

**Trade-off:** Simple but coarse-grained. Gets entire table description even if only one column is needed.

---

#### 🟡 Path B: `schema_chunks.py` + `vector_store.py` (Experimental)

Breaks tables into semantic chunks:

```python
def create_semantic_chunks():
    """
    Instead of 4 documents (one per table),
    create multiple chunks per table
    """
    chunks = [
        # customers table chunks
        {
            "id": "chunk_001",
            "table": "customers",
            "topic": "customer_location",
            "content": "Geographic information about customers including city, state, country",
            "columns": ["customer_id", "location"],
            "relationships": ["orders.customer_id"],
            "sample_values": {"location": ["Silchar", "Guwahati", "Delhi"]}
        },
        {
            "id": "chunk_002",
            "table": "customers",
            "topic": "customer_registration",
            "content": "Customer account lifecycle: creation date, email, status",
            "columns": ["customer_id", "registration_date", "email", "status"],
            "relationships": [],
            "sample_values": {"registration_date": "2024-01-15"}
        },
        # products table chunks
        {
            "id": "chunk_003",
            "table": "products",
            "topic": "product_category",
            "content": "Product classification and categorization",
            "columns": ["product_id", "category"],
            "relationships": ["order_items.product_id"],
            "sample_values": {"category": ["Electronics", "Clothing", "Books"]}
        },
        {
            "id": "chunk_004",
            "table": "products",
            "topic": "product_pricing",
            "content": "Product pricing information",
            "columns": ["product_id", "price"],
            "relationships": [],
            "sample_values": {"price": [99.99, 49.99, 199.99]}
        },
        # orders table chunks
        {
            "id": "chunk_005",
            "table": "orders",
            "topic": "order_status",
            "content": "Order fulfillment state and timing",
            "columns": ["order_id", "order_date", "status"],
            "relationships": ["customers.customer_id", "order_items.order_id"],
            "sample_values": {"status": ["pending", "shipped", "delivered"]}
        },
        # order_items table chunks
        {
            "id": "chunk_006",
            "table": "order_items",
            "topic": "quantity_and_revenue",
            "content": "Line item quantity and revenue calculations",
            "columns": ["order_id", "product_id", "quantity", "unit_price"],
            "relationships": ["orders.order_id", "products.product_id"],
            "sample_values": {"quantity": [1, 5, 10]}
        }
    ]
    return chunks
```

Then these chunks are embedded:

```python
def build_vector_store():
    """
    Each chunk → embedding vector
    """
    for chunk in chunks:
        # Text: chunk["content"] + metadata
        # Model: sentence-transformers/all-MiniLM-L6-v2
        embedding = embedding_model.encode(chunk["content"])
        # embedding is now: [0.023, -0.112, 0.441, ...] (384 dimensions)
        
        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        
        # Store
        embeddings_array.append(embedding)
```

**Flow:**

```
Question: "Where are our customers located?"
    ↓
Embedding: encode question to vector
    ↓
Similarity search: compare against all chunk embeddings
    ↓
Top result: chunk_001 (customer_location) with score 0.87
    ↓
Pass to Gemini with specific chunk context
    ↓
Gemini generates more targeted SQL
```

**Trade-off:** More complex but fine-grained. Gives Gemini exactly what it needs.

---

### Layer 4: SQL Generation

#### `text_to_sql.py`

Calls Gemini API with question + schema context:

```python
def generate_sql(question: str, schema_context: str) -> str:
    """
    Calls Google Gemini API
    
    Prompt includes:
    - User question
    - Relevant schema information (from retrieval)
    - Data dictionary with sample values
    - Example queries (few-shot learning)
    
    Returns: SQL query string
    """
    prompt = f"""
    Given this database schema:
    {schema_context}
    
    Generate a SQL query for: {question}
    
    Requirements:
    - Only SELECT queries allowed
    - Include table aliases
    - Use actual column names
    - Explain your logic
    """
    
    response = gemini_client.generate(prompt)
    return extract_sql_from_response(response)
```

**Example:**

```
Input:
  Question: "Top 5 customers by spending"
  Schema: customers table, orders table, order_items table
  
Output:
  SELECT c.id, c.name, SUM(oi.unit_price * oi.quantity) as total_spending
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  JOIN order_items oi ON o.id = oi.order_id
  GROUP BY c.id, c.name
  ORDER BY total_spending DESC
  LIMIT 5;
```

---

### Layer 5: Validation & Repair

#### `sql_validator.py`

Checks whether generated SQL is safe and valid:

```python
def validate_sql(sql: str) -> bool:
    """
    Checks:
    - Only SELECT (no DROP, INSERT, DELETE, UPDATE)
    - All referenced tables exist
    - All referenced columns exist
    - Column types are compatible
    - No infinite loops or circular references
    """
    if not sql.strip().upper().startswith('SELECT'):
        raise Exception("Only SELECT queries allowed")
    
    # Parse and validate against schema
    ast = parse_sql(sql)
    for table in ast.tables:
        if table not in known_tables:
            raise Exception(f"Unknown table: {table}")
    
    # ... more checks ...
    return True
```

#### `sql_repair.py`

Attempts to fix common SQL generation errors:

```python
def repair_sql(sql: str, error: str) -> str:
    """
    Common error patterns:
    
    1. Column doesn't exist
       "Unknown column 'customer_name'"
       → Fuzzy match to actual column name
       
    2. Table doesn't exist
       "Unknown table 'customer'"
       → Did you mean 'customers'?
       
    3. Missing JOIN condition
       → Infer from foreign keys
    """
    
    if "Unknown column" in error:
        # Extract mentioned column, find closest match
        mentioned = extract_column_name(error)
        closest = fuzzy_match_column(mentioned, all_columns)
        sql = sql.replace(mentioned, closest)
        
    elif "Unknown table" in error:
        mentioned = extract_table_name(error)
        closest = fuzzy_match_table(mentioned, all_tables)
        sql = sql.replace(mentioned, closest)
    
    return sql
```

---

### Layer 6: Database Execution

#### `database_executor.py`

Executes validated SQL safely:

```python
def execute_sql(sql: str):
    """
    1. Connection uses read-only connection (sqlite3 with restricted permissions)
    2. Execute SQL
    3. Return results
    """
    conn = sqlite3.connect(':memory:')
    # Load database in read-only mode
    conn.execute('PRAGMA query_only = ON;')
    
    cursor = conn.execute(sql)
    results = cursor.fetchall()
    
    return results
```

**Safety:** Database connection is read-only. Even if SQL validation failed, no data can be modified.

---

### Layer 7: Result Explanation

#### `result_explainer.py`

Converts raw SQL results to natural language:

```python
def explain_result(question: str, sql: str, results: List) -> str:
    """
    Takes raw query results and explains them to user
    """
    
    # Example:
    # Raw results: [("Alice", 156), ("Bob", 142), ("Carol", 138)]
    # Explanation:
    
    if len(results) == 0:
        return "No results found."
    
    if len(results) == 1 and len(results[0]) == 1:
        # Single number result
        value = results[0][0]
        return f"The answer is {value}."
    
    # Multiple results
    explanation = "The results are:\n"
    for row in results[:5]:  # Top 5
        explanation += f"  - {row[0]}: {row[1]}\n"
    
    if len(results) > 5:
        explanation += f"  ... and {len(results) - 5} more."
    
    return explanation
```

---

### Layer 8: Orchestration

#### `query_engine.py`

Coordinates the entire pipeline:

```python
class QueryEngine:
    def process_question(self, question: str) -> dict:
        """
        Main orchestration logic
        """
        try:
            # Step 1: Retrieve schema context
            schema_context = self.retrieve_schema(question)
            
            # Step 2: Generate SQL
            sql = self.generate_sql(question, schema_context)
            
            # Step 3: Validate
            is_valid = self.validate_sql(sql)
            
            if not is_valid:
                # Step 4: Repair
                sql = self.repair_sql(sql)
                # Validate repaired SQL
                self.validate_sql(sql)
            
            # Step 5: Execute
            results = self.execute_sql(sql)
            
            # Step 6: Explain
            explanation = self.explain_result(question, sql, results)
            
            return {
                "status": "success",
                "question": question,
                "sql": sql,
                "results": results,
                "explanation": explanation
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "question": question
            }
```

---

### Layer 9: API & Frontend

#### `api.py`

FastAPI server:

```python
@app.post("/ask")
def ask_question(request: AskRequest):
    """
    Request:
    {
        "question": "How many orders shipped last week?"
    }
    
    Returns:
    {
        "status": "success",
        "question": "...",
        "sql": "SELECT ...",
        "results": [...],
        "explanation": "..."
    }
    """
    return engine.process_question(request.question)
```

#### `App.tsx`

React frontend:

```typescript
const AskDB: React.FC = () => {
  const [question, setQuestion] = useState("");
  const [results, setResults] = useState(null);
  
  const handleAsk = async () => {
    const response = await fetch("/ask", {
      method: "POST",
      body: JSON.stringify({ question })
    });
    const data = await response.json();
    setResults(data);
  };
  
  return (
    <div>
      <input 
        value={question}
        onChange={e => setQuestion(e.target.value)}
        placeholder="Ask a question about the data..."
      />
      <button onClick={handleAsk}>Ask</button>
      
      {results && (
        <>
          <h3>Generated SQL</h3>
          <code>{results.sql}</code>
          
          <h3>Results</h3>
          <pre>{JSON.stringify(results.results, null, 2)}</pre>
          
          <h3>Explanation</h3>
          <p>{results.explanation}</p>
        </>
      )}
    </div>
  );
};
```

---

## ⚙️ How It Works End-to-End

### Concrete Example

**User asks:** "Which customers from California had orders last week?"

**Step 1: React frontend**
```
Input: "Which customers from California had orders last week?"
       ↓
       POST /ask
```

**Step 2: Query Engine retrieval**
```
Question: "Which customers from California had orders last week?"
       ↓
Legacy path: Retrieves customers + orders documents
    OR
Experimental path: 
  - Embeds question
  - Finds chunk_001 (customer_location) - score 0.91
  - Finds chunk_005 (order_status) - score 0.88
  - Passes these chunks to Gemini
```

**Step 3: SQL generation**
```
Gemini receives:
  Question: "Which customers from California had orders last week?"
  Schema: [relevant tables/columns]
  
Generates:
  SELECT DISTINCT c.name, c.location
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  WHERE c.location = 'California'
  AND o.order_date >= DATE('now', '-7 days')
```

**Step 4: Validation**
```
Check:
  ✓ Only SELECT query
  ✓ customers table exists
  ✓ orders table exists
  ✓ All columns exist
  ✓ No dangerous operations
  
Status: Valid
```

**Step 5: Execution**
```
Results:
  [
    ("Alice Johnson", "California"),
    ("Bob Smith", "California"),
    ("Carol White", "California")
  ]
```

**Step 6: Explanation**
```
"Three customers from California placed orders in the last week:
 Alice Johnson, Bob Smith, and Carol White."
```

**Step 7: Return to frontend**
```
{
  "status": "success",
  "question": "Which customers from California had orders last week?",
  "sql": "SELECT DISTINCT c.name, c.location ...",
  "results": [...],
  "explanation": "Three customers from California..."
}
```

**Step 8: Display**
```
Frontend shows:
  ✓ The question
  ✓ The generated SQL (for transparency)
  ✓ The results in a table
  ✓ The natural language explanation
```

---

## 🎯 Key Technical Insights

### 1. The Bridge Between Languages

AskDB is fundamentally about building a bridge:

```
Human Language          Database Schema          SQL
    ↕                        ↕                    ↕
"customers from            (customers.location   SELECT ...
California"               = 'California')        WHERE location = 'CA'
```

The more precise this bridge, the better the SQL generation.

### 2. Two Retrieval Approaches

**Table-level (Legacy - Production):**
```
Question → 4 table documents → LLM sees all columns → SQL
```

**Chunk-level (Experimental):**
```
Question → Semantic embedding → 2-3 targeted chunks → LLM sees only relevant columns → SQL
```

The experiment tests: Does targeted context produce better SQL?

### 3. Safety by Layering

```
Layer 1: LLM generates SQL (might be wrong)
         ↓
Layer 2: Validator checks (catches most errors)
         ↓
Layer 3: Repair attempts fix (handles common issues)
         ↓
Layer 4: DB connection is read-only (final safety net)
```

Even if everything fails, the database can't be modified.

### 4. Why Not Integrate Experimental Yet?

**Bad approach:**
```
Replace legacy → SQL accuracy ↓ → Don't know why → Revert
```

**Good approach (current):**
```
Run both in parallel → Compare results → Only integrate if experimental wins
```

This is proper experimental design.

### 5. Sample Values Are Critical

The difference between:

```
location TEXT
```

and:

```
location TEXT
Sample: Silchar, Guwahati, Delhi, Mumbai
```

The LLM uses these clues to understand what goes in each column. Without them, it might try:

```sql
WHERE location = 123  -- Wrong! location is text, not numbers
```

---

## 🚀 Getting Started

### Prerequisites

```bash
python3.10+
sqlite3
pip
```

### Installation

```bash
# Clone repo
git clone https://github.com/yourusername/askdb.git
cd askdb

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Setup

```bash
# 1. Create .env file
cat > .env << EOF
GEMINI_API_KEY=your_api_key_here
DATABASE_PATH=./data/askdb.db
EOF

# 2. Initialize database
python create_db.py
# ✓ Database created at ./data/askdb.db
# ✓ Schema initialized
# ✓ Sample data seeded

# 3. Extract schema
python schema_extractor.py
# ✓ Schema extracted

# 4. Build retrieval indices
python retrieval/schema_documents.py
# ✓ Legacy retrieval ready

python retrieval/schema_chunks.py
python retrieval/vector_store.py
# ✓ Experimental retrieval ready (optional)

# 5. Start API
python api.py
# INFO: Server running on http://localhost:8000
```

### Test

```bash
# Terminal 1: API running (see above)

# Terminal 2: Test a query
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How many customers are from California?"}'

# Response:
{
  "status": "success",
  "question": "How many customers are from California?",
  "sql": "SELECT COUNT(*) FROM customers WHERE location = 'California'",
  "results": [[342]],
  "explanation": "There are 342 customers from California in the database."
}
```

---

## 🔧 API Reference

### POST /ask

**Request:**
```json
{
  "question": "What are the top 5 products by revenue?"
}
```

**Response:**
```json
{
  "status": "success",
  "question": "What are the top 5 products by revenue?",
  "sql": "SELECT p.name, SUM(oi.unit_price * oi.quantity) as revenue FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id ORDER BY revenue DESC LIMIT 5",
  "results": [
    ["Premium Widget", 125000],
    ["Deluxe Gadget", 98500],
    ["Ultra Tool", 87300]
  ],
  "explanation": "The top products by revenue are Premium Widget ($125k), Deluxe Gadget ($98.5k), and Ultra Tool ($87.3k)."
}
```

---

## 📊 Evaluation & Improvements

### Testing Framework

```bash
python evaluate.py
```

This compares:
- Legacy retrieval accuracy
- Experimental retrieval accuracy
- Which performs better on different query types

**Output:**
```
Evaluation Results
════════════════════════════════════════

Legacy (Table-Level Retrieval):
  Total tests: 50
  Passed: 47
  Accuracy: 94%
  
Experimental (Chunk-Level Retrieval):
  Total tests: 50
  Passed: 45
  Accuracy: 90%
  
Recommendation: Keep legacy as default
Next step: Improve chunk selection for experimental
```

### The Ultimate Goal

Eventually, experimental should win on accuracy. Then you can switch:

```python
# In query_engine.py
RETRIEVAL_METHOD = "experimental"  # Flip the switch
```

---

## 📋 File Responsibility Chart

| File | Responsibility | Status |
|------|-----------------|--------|
| `schema.sql` | DB schema definition | 🟢 Core |
| `create_db.py` | Creates database | 🟢 Core |
| `schema_extractor.py` | Introspects schema | 🟢 Core |
| `schema_documents.py` | Table-level docs | 🟢 Production |
| `schema_chunks.py` | Semantic chunks | 🟡 Experimental |
| `vector_store.py` | Vector index | 🟡 Experimental |
| `chunk_embeddings.npy` | Stored embeddings | 🟡 Experimental |
| `chunk_metadata.json` | Chunk metadata | 🟡 Experimental |
| `text_to_sql.py` | NL → SQL (Gemini) | 🟢 Core |
| `sql_validator.py` | SQL safety check | 🟢 Core |
| `sql_repair.py` | Fix broken SQL | 🟢 Core |
| `database_executor.py` | Execute SQL | 🟢 Core |
| `result_explainer.py` | SQL → NL | 🟢 Core |
| `query_engine.py` | Orchestration | 🟢 Core |
| `api.py` | FastAPI server | 🟢 Core |
| `App.tsx` | React frontend | 🟢 Core |
| `evaluate.py` | Testing framework | 🟢 Evaluation |
| `test_queries.json` | Test cases | 🟢 Evaluation |

---

## 💡 The Strongest Way to Describe This Project

### On Resume

> Built AskDB, a schema-aware natural-language-to-SQL system that converts user questions into validated read-only SQL queries using Gemini, with automatic SQL repair and result explanation. Implemented a local semantic retrieval layer using Sentence Transformers to retrieve fine-grained database schema chunks, enabling controlled experimentation and comparison against existing table-level schema retrieval to evaluate improvements in SQL generation quality.

### In Interview

"AskDB bridges three languages: human language, database schema, and SQL. The innovation isn't just using an LLM—it's the dual retrieval architecture that lets us experiment with semantic understanding without risking production stability. We're testing whether chunk-level retrieval produces better SQL than table-level retrieval by running both paths in parallel and comparing accuracy metrics."

---

## 🤝 Contributing

```bash
# Add a test case
# Edit test_queries.json with new question
{
  "question": "Your question here",
  "expected_sql": "SELECT ...",
  "difficulty": "easy|medium|hard"
}

# Run evaluation
python evaluate.py

# If you improve something:
git checkout -b feature/improvement
# ... make changes ...
git push origin feature/improvement
# → Open pull request
```

---

## 📄 License

MIT License - see LICENSE file

---

## 🙏 Acknowledgments

- Powered by Google Gemini API
- Embeddings via Hugging Face Sentence Transformers (all-MiniLM-L6-v2)
- Built with FastAPI and React
- SQLite for database layer

---

<div align="center">

**Bridging Human Language → Database Schema → SQL**

[⭐ Star on GitHub](https://github.com/yourusername/askdb)

</div>