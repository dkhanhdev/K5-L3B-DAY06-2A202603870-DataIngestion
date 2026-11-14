"""TODO: store and search vectors using PostgreSQL + pgvector."""
from typing import Any
from .models import Chunk
import math
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        """TODO: retain connection settings; validate model dimensions."""
        if not isinstance(dimensions, int) or not 1 <= dimensions <= 16000:
            raise ValueError("Invalid vector dimensions")
        self.database_url = database_url
        self.dimensions = dimensions

    def connect(self):
        return psycopg.connect(self.database_url, connect_timeout=10, row_factory=dict_row)

    def _vector(self, values):
        if len(values) != self.dimensions or not all(math.isfinite(v) for v in values):
            raise ValueError("Invalid vector length or nonfinite values")
        if sum(v*v for v in values) == 0:
            raise ValueError("Zero vector cannot use cosine similarity")
        return "[" + ",".join(str(float(v)) for v in values) + "]"

    def create_schema(self) -> None:
        """TODO: create table with vector column and source/page/filter metadata."""
        with self.connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute(f"""CREATE TABLE IF NOT EXISTS day6_chunks (
                strategy text NOT NULL, chunk_id text NOT NULL, document_id text NOT NULL,
                source text NOT NULL, page integer NOT NULL, text text NOT NULL,
                metadata jsonb NOT NULL, embedding vector({self.dimensions}) NOT NULL,
                PRIMARY KEY(strategy, chunk_id))""")
            row = conn.execute("SELECT format_type(atttypid,atttypmod) AS type FROM pg_attribute WHERE attrelid='day6_chunks'::regclass AND attname='embedding'").fetchone()
            if row["type"] != f"vector({self.dimensions})":
                raise ValueError("Existing table has incompatible dimensions")

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """TODO: validate lengths/dimensions and write stable IDs without duplicates.

        When re-ingesting changed source documents, remove obsolete chunks too.
        """
        if len(chunks) != len(vectors) or len({c.chunk_id for c in chunks}) != len(chunks):
            raise ValueError("Mismatched vectors or duplicate chunk IDs")
        rows = [(strategy, c.chunk_id, c.document_id, c.source, c.page, c.text,
                 Jsonb(c.metadata), self._vector(v)) for c, v in zip(chunks, vectors)]
        # Full strategy snapshot replacement in one transaction removes obsolete chunks.
        # Only this lab's table and this strategy are affected; failure rolls back.
        with self.connect() as conn:
            conn.execute("SELECT pg_advisory_xact_lock(6230626)")
            conn.execute("DELETE FROM day6_chunks WHERE strategy=%s", (strategy,))
            with conn.cursor() as cur:
                cur.executemany("INSERT INTO day6_chunks VALUES (%s,%s,%s,%s,%s,%s,%s,%s::vector)", rows)

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """TODO: filter permitted metadata in SQL, rank by cosine distance, return top-k.

        Return chunk ID, text, score and metadata. Parameterize user-supplied values.
        """
        allowed = {"section", "year", "version", "category", "audience", "language", "chapter"}
        if filters and not set(filters) <= allowed:
            raise ValueError("Unsupported metadata filter")
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be positive")
        vector = self._vector(query_vector)
        with self.connect() as conn:
            rows = conn.execute("""SELECT chunk_id, document_id, source, page, text, metadata,
                1 - (embedding <=> %s::vector) AS score FROM day6_chunks
                WHERE strategy=%s AND metadata @> %s
                ORDER BY embedding <=> %s::vector, chunk_id LIMIT %s""",
                (vector, strategy, Jsonb(filters or {}), vector, top_k)).fetchall()
        return rows

    def snapshot(self, strategy):
        with self.connect() as conn:
            return conn.execute("SELECT chunk_id, md5(text || metadata::text || embedding::text) AS hash FROM day6_chunks WHERE strategy=%s ORDER BY chunk_id", (strategy,)).fetchall()

    def versions(self):
        with self.connect() as conn:
            return conn.execute("SELECT current_setting('server_version') AS postgresql, extversion AS pgvector FROM pg_extension WHERE extname='vector'").fetchone()
