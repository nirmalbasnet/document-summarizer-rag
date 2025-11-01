from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter



class Chunking:
    def get_chunks(self, document_name, file_path):
        loader = PyPDFLoader(file_path)
        pdf_doc = loader.load()

        for d in pdf_doc:
            md = d.metadata or {}
            md.update({"document_name": document_name, "file_path": str(file_path)})
            d.metadata = md

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        split_docs = splitter.split_documents(pdf_doc)
        
        return [Document(page_content=d.page_content, metadata=d.metadata or {}) for d in split_docs]









# def chunk_reviews(reviews, metadata):
#     """Convert list of reviews into LangChain Documents with metadata."""
#     docs = []
#     for review in reviews:
#         docs.append(
#             Document(
#                 page_content=review,
#                 metadata=metadata
#             )
#         )
#     return docs

# def embed_and_store(docs, persist_directory="chroma_store"):
#     # Text splitter: splits large docs into smaller chunks
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=500,
#         chunk_overlap=50
#     )

#     split_docs = splitter.split_documents(docs)


#     # Create embeddings
#     embeddings = get_embeddings()

#     # Store in Chroma
#     return ch.from_documents(
#         documents=split_docs,
#         embedding=embeddings,
#         persist_directory=persist_directory,
#         collection_name="reviews"
#     )

