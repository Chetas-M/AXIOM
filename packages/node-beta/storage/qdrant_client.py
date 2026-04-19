from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
import os

QDRANT_HOST = os.getenv("QDRANT_HOST", "node-alpha")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def init_qdrant():
    client = get_qdrant_client()
    collection_name = "news_docs"
    
    if not client.collection_exists(collection_name=collection_name):
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        
        from qdrant_client.http.models import PayloadSchemaType
        client.create_payload_index(collection_name, field_name="ticker", field_schema=PayloadSchemaType.KEYWORD)
        client.create_payload_index(collection_name, field_name="published_at", field_schema=PayloadSchemaType.INTEGER)
        client.create_payload_index(collection_name, field_name="source", field_schema=PayloadSchemaType.KEYWORD)
        client.create_payload_index(collection_name, field_name="url", field_schema=PayloadSchemaType.KEYWORD)
        
        print(f"Collection {collection_name} created and indexed.")
    else:
        print(f"Collection {collection_name} already exists.")

if __name__ == "__main__":
    init_qdrant()
