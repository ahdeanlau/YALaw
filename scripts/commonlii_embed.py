#!/usr/bin/env python3
"""
Embed every JSON file under `output_probe/` and upload all vectors to Qdrant.

Edit the CONFIG block below to suit your project.
"""
import sys
import os
import re
import math


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os
from typing import Iterator, List
from embeddings.embeddings import OpenAIEmbedder          # <- your class
from qdrant_client.http.models import PointStruct

# ─── CONFIG ────────────────────────────────────────────────────────────────────
ROOT_DIR            = "/Users/dlau/Documents/GitHub/YALaw/output_probe/"  # folder to scan (recursive)
JSON_FIELD          = "full_text"      # field to embed (dot-notation OK)
ID_FIELD            = "id"                      # field for the vector ID
QDRANT_COLLECTION   = "commonlii_cases"        # Qdrant collection name
SAVE_DUCKDB_PATH    = "commonlii_cases.duckdb"   # set to None to skip local save
# ───────────────────────────────────────────────────────────────────────────────


def iter_json_files(root: str) -> Iterator[str]:
    """Yield full paths of *.json files under `root` (recursive)."""
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if name.lower().endswith(".json"):
                yield os.path.join(dirpath, name)


def main() -> None:
    embedder = OpenAIEmbedder()
    all_points: List[PointStruct] = []

    for path in iter_json_files(ROOT_DIR):
        embedder.logger.info("→ Embedding %s", path)
        try:
            pts = embedder.embed_json_file(
                json_file_path=path,
                json_field=JSON_FIELD,
                id_field=ID_FIELD,
            )
            all_points.extend(pts)
        except Exception as exc:
            embedder.logger.error("🔄  Retrying %s (%s)", path, exc)
            embedder.logger.info("Attempting to embed %s in chunks", path)
            
            # Default chunk count in case parsing fails
            num_of_chunks = 3

            # Try to extract token information from the exception message
            try:
                exc_str = str(exc)
                match = re.search(r'you requested (\d+) tokens', exc_str)
                if match:
                    requested_tokens = int(match.group(1))
                    # Use a default or known max_tokens, e.g., 8192
                    MAX_TOKENS = 8192
                    num_of_chunks = math.ceil(requested_tokens / MAX_TOKENS)
                    embedder.logger.info("Requested %d tokens. Chunking into %d parts (max %d tokens each).",
                                        requested_tokens, num_of_chunks, MAX_TOKENS)
            except Exception as parse_exc:
                embedder.logger.warning("⚠️  Failed to parse token info from error: %s", parse_exc)

            try:
                pts = embedder.embed_json_file_in_chunks(
                    json_file_path=path,
                    json_field=JSON_FIELD,
                    id_field=ID_FIELD,
                    num_of_chunks=num_of_chunks
                )
                all_points.extend(pts)
                embedder.logger.info("✅  Successfully embedded %s in chunks (added %d points to all_points)", path, len(pts))
            except Exception as chunk_exc:
                embedder.logger.error("⚠️  FAILED to embed %s in %d chunks (%s)", path, num_of_chunks, chunk_exc)
            

    if not all_points:
        raise RuntimeError("No embeddings were created — check CONFIG settings.")

    # Optional local backup
    if SAVE_DUCKDB_PATH:
        embedder.upload_points_to_duckdb(all_points, db_path=SAVE_DUCKDB_PATH)

    # Chunked upload to Qdrant: 10 points at a time
    # BATCH_SIZE = 10
    # for i in range(0, len(all_points), BATCH_SIZE):
    #     chunk = all_points[i:i + BATCH_SIZE]
    #     embedder.upload_points_to_qdrant(chunk, collection_name=QDRANT_COLLECTION)
    #     embedder.logger.info("🔼 Uploaded points %d to %d", i + 1, i + len(chunk))
    #     # Optional delay to reduce Qdrant server load

    # embedder.logger.info("✅ %d total points uploaded to '%s'",
    #                      len(all_points), QDRANT_COLLECTION)


if __name__ == "__main__":
    main()
