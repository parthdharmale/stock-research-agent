import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

class VectorMemoryManager:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, "../../chroma_db")

        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        self.vector_store = Chroma(
            collection_name="historical_research_reports",
            embedding_function=self.embeddings,
            persist_directory=db_path
        )

    def save_report(self, ticker: str, report_content: str):
        """Saves a final generated report into long-term vector memory."""
        doc = Document(
            page_content=report_content,
            metadata={"ticker": ticker, "type": "final_report"}
        )
        self.vector_store.add_documents([doc])
        print(f"MEMORY: Succesfully archived report for {ticker} into Vector DB.")

    def query_archives(self, query: str, ticker: str = None, k: int=2) -> str:
        """Searches past reports for semantic context."""
        #Opional filter to only search reports for a specific stock.
        filter_dict = {"ticker": ticker} if ticker else None

        results = self.vector_store.similarity_search(
            query,
            k=k,
            filter=filter_dict
        )

        if not results:
            return "No historical internal reports found for this query"
        
        # Compile the retrieved memories into a single string
        compiled_memory = "\n\n--- PAST ARCHIVED KNOWLEDGE---\n"

        for i, doc in enumerate(results):
            compiled_memory += f"Archive {i+1}: \n{doc.page_content[:1000]}...\n"

        return compiled_memory

memory_manager = VectorMemoryManager()