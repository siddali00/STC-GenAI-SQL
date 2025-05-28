# schema_index_qdrant.py

import os, pickle
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
import cohere
from database import Base

# ── 1) Load config from env ──
QDRANT_URL     = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# ── 2) Init clients ──
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, check_compatibility=False)
co      = cohere.Client(COHERE_API_KEY)

# ── 3) Build schema entries ──
entries = []
for table in Base.metadata.sorted_tables:
    for col in table.columns:
        desc = f"`{table.name}.{col.name}` column of type {col.type}"
        entries.append({
            "id":      len(entries),
            "table":   table.name,
            "column":  col.name,
            "text":    desc
        })

# ── 4) Embed descriptions ──
texts  = [e["text"] for e in entries]
resp   = co.embed(model="embed-multilingual-v2.0", texts=texts)
embeds = resp.embeddings

# ── 5) Create or reset the Qdrant collection ──
COLL = "stc-schema"      # <- pick one name and stick to it
dim  = len(embeds[0])

# Delete if exists, then create
if qdrant.get_collection(COLL):
    qdrant.delete_collection(collection_name=COLL)

qdrant.create_collection(
    collection_name=COLL,
    vectors_config=rest.VectorParams(size=dim, distance=rest.Distance.COSINE),
)

# ── 6) Upsert points into that same collection ──
points = [
    rest.PointStruct(
        id=e["id"],
        vector=embeds[i],
        payload={"table": e["table"], "column": e["column"], "desc": e["text"]}
    )
    for i, e in enumerate(entries)
]
qdrant.upsert(collection_name=COLL, points=points)

# ── 7) Persist metadata for lookups ──
with open("schema_meta.pkl", "wb") as f:
    pickle.dump(entries, f)

print(f"✅ Schema indexed into Qdrant (collection ‘{COLL}’).")
