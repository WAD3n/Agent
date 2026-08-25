import os

import duckdb

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge_base.duckdb")

KNOWLEDGE_BASE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "knowledge_base_search",
        "description": "Search the curated knowledge base for relevant documents.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return.",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
}


def _get_connection() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(DB_PATH)
    con.install_extension("vss")
    con.load_extension("vss")
    return con


def knowledge_base_search(query: str, top_k: int = 3) -> str:
    # TODO: embed `query` with Gemini and run a vector similarity search
    # (vss HNSW index) against the `documents` table once the corpus is ingested.
    raise NotImplementedError("Knowledge base not ingested yet.")
