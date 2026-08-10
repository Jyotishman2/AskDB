import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rag.schema_chunks import create_schema_chunks


BASE_DIR = Path(__file__).resolve().parent
VECTOR_DIR = BASE_DIR / "vector_data"
EMBEDDINGS_FILE = VECTOR_DIR / "chunk_embeddings.npy"
METADATA_FILE = VECTOR_DIR / "chunk_metadata.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_MIN_SIMILARITY = float(os.getenv("ASKDB_MIN_SIMILARITY", "0.12"))

model = SentenceTransformer(MODEL_NAME)


def build_vector_store(force_rebuild=False):
    if force_rebuild and VECTOR_DIR.exists():
        for old_file in VECTOR_DIR.iterdir():
            if old_file.is_file():
                old_file.unlink()

    if EMBEDDINGS_FILE.exists() and METADATA_FILE.exists() and not force_rebuild:
        print(f"Vector index already exists at {VECTOR_DIR}.")
        return

    chunks = create_schema_chunks()
    texts = [chunk["content"] for chunk in chunks]
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_FILE, embeddings.astype(np.float32))

    with open(METADATA_FILE, "w", encoding="utf-8") as file:
        json.dump(chunks, file, indent=2, ensure_ascii=False)

    print(f"Created vector store with {len(chunks)} schema chunks.")


def load_vector_store():
    if not EMBEDDINGS_FILE.exists() or not METADATA_FILE.exists():
        build_vector_store()

    embeddings = np.load(EMBEDDINGS_FILE)

    with open(METADATA_FILE, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    return embeddings, metadata


def retrieve_vector_schema(question, top_k=5, min_score=None):
    if top_k <= 0:
        return []

    if min_score is None:
        min_score = DEFAULT_MIN_SIMILARITY

    embeddings, metadata = load_vector_store()

    query_embedding = model.encode(
        [question],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )[0]

    scores = embeddings @ query_embedding
    ranked_indices = np.argsort(scores)[::-1]

    results = []

    for index in ranked_indices[:top_k]:
        score = float(scores[index])
        if score < min_score:
            continue

        chunk = metadata[int(index)]
        results.append(
            {
                "id": chunk["id"],
                "table": chunk["table"],
                "topic": chunk["topic"],
                "content": chunk["content"],
                "score": score,
            }
        )

    return results


def _print_retrieval_results(question, top_k=5, min_score=None):
    results = retrieve_vector_schema(question, top_k=top_k, min_score=min_score)

    print(f"QUESTION: {question}")
    print(f"TOP_K: {top_k} | MIN_SCORE: {min_score if min_score is not None else DEFAULT_MIN_SIMILARITY}")

    if not results:
        print("No chunks met the similarity threshold.")
        return

    for result in results:
        print("-" * 70)
        print(f"TABLE: {result['table']}")
        print(f"TOPIC: {result['topic']}")
        print(f"SIMILARITY SCORE: {result['score']:.4f}")

    print("-" * 70)


def _run_demo_queries():
    questions = [
        "How many customers are from Assam?",
        "What products generated the most sales?",
        "Which customers generated the highest revenue?",
        "How many orders were cancelled?",
        "Which product category generated the highest revenue?",
    ]

    for question in questions:
        print()
        _print_retrieval_results(question, top_k=5, min_score=DEFAULT_MIN_SIMILARITY)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chunk-level schema RAG for AskDB")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild the local vector index")
    parser.add_argument("--question", type=str, help="Retrieve schema chunks for a single question")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to return")
    parser.add_argument("--min-score", type=float, default=None, help="Minimum similarity threshold")
    parser.add_argument("--test", action="store_true", help="Run the local retrieval demo questions")
    args = parser.parse_args()

    if args.rebuild:
        build_vector_store(force_rebuild=True)

    if args.question:
        _print_retrieval_results(args.question, top_k=args.top_k, min_score=args.min_score)
    elif args.test:
        _run_demo_queries()
    else:
        print("Use --rebuild, --question, or --test.")