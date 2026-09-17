"""ChromaDB vector store — persistent, local, free."""
import chromadb
import uuid


class VectorStore:
    def __init__(self, embedder, collection_name="study_notes", persist_dir=".chroma"):
        self.embedder = embedder
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_chunks(self, chunks, source="unknown"):
        if not chunks:
            raise ValueError(
                "No text could be extracted from this document — nothing to index. "
                "If it is a scanned/image-based PDF, it needs OCR first."
            )
        # Idempotent per source: replace any earlier copy of the same document
        # instead of duplicating its chunks on re-upload.
        self.remove_source(source)
        embeddings = self.embedder.embed(chunks)
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"source": source} for _ in chunks]
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )

    def search(self, query, k=4):
        q_emb = self.embedder.embed(query)[0]
        results = self.collection.query(query_embeddings=[q_emb], n_results=k)
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        return [{"text": d, "source": m["source"]} for d, m in zip(docs, metas)]

    def remove_source(self, source):
        """Delete every chunk belonging to the given document source."""
        try:
            got = self.collection.get(where={"source": source})
            ids = got.get("ids") or []
            if ids:
                self.collection.delete(ids=ids)
        except Exception:
            pass

    def list_sources(self):
        """Return unique document sources currently in the collection."""
        if self.collection.count() == 0:
            return []
        metas = self.collection.get(include=["metadatas"])["metadatas"]
        return sorted({m["source"] for m in metas if m and m.get("source")})

    def reset(self):
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
