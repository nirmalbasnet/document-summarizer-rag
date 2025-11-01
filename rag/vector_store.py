import os
import logging
from pathlib import Path
from langchain_chroma import Chroma as ch
from rag.aws_bedrock_model import get_embeddings_model

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
         # ensure persist directory is inside project and exists
        base_dir = Path(__file__).parent.parent.resolve()
        self.persist_directory = str((base_dir / "chroma_store").resolve())
        self.collection_name = "documents"

        try:
            os.makedirs(self.persist_directory, exist_ok=True)
        except Exception as e:
            logger.error(f"Could not create persist dir {self.persist_directory}: {e}")
            raise

        if not os.access(self.persist_directory, os.W_OK):
            logger.error(f"Persist directory not writable: {self.persist_directory}")
            raise PermissionError(f"Persist directory not writable: {self.persist_directory}")

    def is_document_already_ingested(self, metadata):
        vector_db = ch(
            persist_directory=self.persist_directory,
            embedding_function=get_embeddings_model(),
            collection_name=self.collection_name
        )

        results = vector_db.similarity_search("dummy", k=1, filter=metadata)
        return len(results) > 0
    
    def add_documents_from_chunks(self, chunks, document_name, file_path):
        embeddings=get_embeddings_model()

        for c in chunks:
            md = c.metadata or {}
            md.update({"document_name": document_name, "file_path": str(file_path)})
            c.metadata = md
            c.page_content = f"Document Name: {document_name}\nFile Path: {file_path}\n{c.page_content}"

        return ch.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=self.persist_directory,
            collection_name=self.collection_name
        )
    
    def get_retriever(self, k=3):
        embeddings = get_embeddings_model()
        vector_store = ch(
            persist_directory=self.persist_directory,
            embedding_function=embeddings,
            collection_name=self.collection_name
        )
        
        return vector_store.as_retriever(search_kwargs={"k": k})
    
    def delete_document_vectors(self, document_name: str):
        try:
            vector_db = ch(
                persist_directory=self.persist_directory,
                embedding_function=get_embeddings_model(),
                collection_name=self.collection_name
            )

            vector_db.delete(
                where={"document_name": document_name}  # match metadata
            )
            
            print(f"Deleted vectors for {document_name}")
            return True
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            return False
        
    def get_available_documents(self):
        vector_db = ch(
            persist_directory=self.persist_directory,
            embedding_function=get_embeddings_model(),
            collection_name=self.collection_name
        )

        # Use metadata query to get all documents
        docs = vector_db.get()
        
        metadatas = docs.get("metadatas") 
        
        document_names = set()

        for idx, md in enumerate(metadatas):
            if not isinstance(md, dict):
                continue
            name = md.get("document_name")
            if name in document_names:
                continue
            document_names.add(name)
        
        return document_names