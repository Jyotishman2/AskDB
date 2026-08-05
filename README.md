# Text-to-SQL RAG

This project provides a starter structure for a text-to-SQL retrieval-augmented generation workflow with an ecommerce-style dataset.

## Project layout

- `data/` stores raw CSV inputs and dataset metadata.
- `database/` contains SQL schema and database initialization logic.
- `backend/` hosts API or service code.
- `rag/` contains retrieval and generation logic.
- `frontend/` contains user-facing interface code.
- `evaluation/` contains evaluation and testing scripts.

## Getting started

1. Install the dependencies from `requirements.txt`.
2. Run `python database/create_db.py` to build the SQLite database.
3. Start building the backend, RAG pipeline, and frontend components.
