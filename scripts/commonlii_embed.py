#!/usr/bin/env python3
"""
Embed every JSON file under `output_probe/` and upload all vectors to Qdrant.

Edit the CONFIG block below to suit your project.
"""

import os
from typing import Iterator, List
from embeddings.embeddings import OpenAIEmbedder          # <- your class
from qdrant_client.http.models import PointStruct

# ─── CONFIG ────────────────────────────────────────────────────────────────────
ROOT_DIR            = "/Users/dlau/Documents/GitHub/YALaw/output_probe"  # folder to scan (recursive)
JSON_FIELD          = "full_text"      # field to embed (dot-notation OK)
ID_FIELD            = None                      # field for the vector ID
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
            embedder.logger.error("⚠️  Skipped %s (%s)", path, exc)

    if not all_points:
        raise RuntimeError("No embeddings were created — check CONFIG settings.")

    # One bulk upload for efficiency
    embedder.upload_points_to_qdrant(all_points, collection_name=QDRANT_COLLECTION)

    # Optional local backup
    if SAVE_DUCKDB_PATH:
        embedder.upload_points_to_duckdb(all_points, db_path=SAVE_DUCKDB_PATH)

    embedder.logger.info("✅ %d total points uploaded to '%s'",
                         len(all_points), QDRANT_COLLECTION)


if __name__ == "__main__":
    main()
