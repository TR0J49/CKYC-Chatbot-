"""
RAG Engine Module for Novio AI Assistant
Using LangGraph for graph-based workflow orchestration
"""

import os
from typing import List, Dict, Any, TypedDict, Annotated
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

load_dotenv()

# Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b-cloud")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", 3))
COMPANY_NAME = os.getenv("COMPANY_NAME", "Novio")
LEGAL_ENTITY = os.getenv("LEGAL_ENTITY", "Credilio Financial Technologies Pvt. Ltd.")
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.3))

# FAISS index path
FAISS_INDEX_PATH = "data/faiss_index"


# ============== State Definition ==============
class GraphState(TypedDict):
    """State for the RAG graph workflow."""
    query: str
    documents: List[Dict[str, Any]]
    generation: str
    source: str
    confidence: float
    context_used: int


# ============== Vector Store ==============
class VectorStore:
    """FAISS-based vector store for document retrieval."""

    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.documents: List[str] = []
        self.dimension = 384  # all-MiniLM-L6-v2 embedding dimension
        self._initialize()

    def _initialize(self):
        """Initialize the embedding model and load/create FAISS index."""
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)

        if self._load_index():
            print("Loaded existing FAISS index")
        else:
            print("Creating new FAISS index")
            self.index = faiss.IndexFlatIP(self.dimension)

    def _load_index(self) -> bool:
        """Load FAISS index and documents from disk."""
        index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
        docs_file = os.path.join(FAISS_INDEX_PATH, "documents.json")

        if os.path.exists(index_file) and os.path.exists(docs_file):
            try:
                self.index = faiss.read_index(index_file)
                with open(docs_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                return True
            except Exception as e:
                print(f"Error loading index: {e}")
                return False
        return False

    def _save_index(self):
        """Save FAISS index and documents to disk."""
        os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
        index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
        docs_file = os.path.join(FAISS_INDEX_PATH, "documents.json")

        faiss.write_index(self.index, index_file)
        with open(docs_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f)

        print(f"Index saved to {FAISS_INDEX_PATH}")

    def add_documents(self, documents: List[str]):
        """Add documents to the vector store."""
        if not documents:
            return

        print(f"Adding {len(documents)} documents to index")

        embeddings = self.embedding_model.encode(documents, normalize_embeddings=True)
        embeddings = np.array(embeddings).astype('float32')

        self.index.add(embeddings)
        self.documents.extend(documents)
        self._save_index()

        print(f"Index now contains {self.index.ntotal} vectors")

    def similarity_search(self, query: str, k: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if self.index.ntotal == 0:
            return []

        query_embedding = self.embedding_model.encode([query], normalize_embeddings=True)
        query_embedding = np.array(query_embedding).astype('float32')

        scores, indices = self.index.search(query_embedding, min(k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents) and idx >= 0:
                results.append({
                    "content": self.documents[idx],
                    "score": float(score)
                })

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_model": EMBEDDING_MODEL
        }


# ============== LangGraph Nodes ==============

# Initialize components
vector_store = None
llm = None


def get_vector_store() -> VectorStore:
    """Get or create the vector store singleton."""
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store


def get_llm() -> ChatOllama:
    """Get or create the LLM singleton."""
    global llm
    if llm is None:
        llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.7,
        )
    return llm


# Node 1: Retrieve documents
def retrieve_documents(state: GraphState) -> GraphState:
    """Retrieve relevant documents from the vector store."""
    print(f"---RETRIEVE DOCUMENTS---")

    query = state["query"]
    vs = get_vector_store()
    documents = vs.similarity_search(query, k=TOP_K_RESULTS)

    print(f"Retrieved {len(documents)} documents")

    return {
        **state,
        "documents": documents,
        "confidence": documents[0]["score"] if documents else 0.0,
        "context_used": len(documents)
    }


# Node 2: Grade documents (decide if relevant)
def grade_documents(state: GraphState) -> GraphState:
    """Grade whether retrieved documents are relevant."""
    print(f"---GRADE DOCUMENTS---")

    documents = state["documents"]
    confidence = state["confidence"]

    if documents and confidence > SIMILARITY_THRESHOLD:
        print(f"Documents are RELEVANT (confidence: {confidence:.3f})")
        return {**state, "source": "faq"}
    else:
        print(f"Documents NOT relevant (confidence: {confidence:.3f}), using fallback")
        return {**state, "source": "ai", "documents": []}


# Node 3: Generate response with RAG context
def generate_rag_response(state: GraphState) -> GraphState:
    """Generate response using retrieved context."""
    print(f"---GENERATE RAG RESPONSE---")

    query = state["query"]
    documents = state["documents"]

    context = "\n\n".join([doc["content"] for doc in documents])

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a helpful customer support assistant for {COMPANY_NAME} ({LEGAL_ENTITY}),
a fintech platform offering FD-backed RuPay credit cards in India.

Based on the following context from our FAQ documentation, please answer the user's question.
Be concise, helpful, and professional. Use bullet points for lists when appropriate.

Context:
{context}"""),
        ("human", "{query}")
    ])

    chain = prompt | get_llm()
    response = chain.invoke({"query": query})

    return {
        **state,
        "generation": response.content
    }


# Node 4: Generate fallback response (no context)
def generate_fallback_response(state: GraphState) -> GraphState:
    """Generate response using LLM's general knowledge."""
    print(f"---GENERATE FALLBACK RESPONSE---")

    query = state["query"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a helpful customer support assistant for {COMPANY_NAME} ({LEGAL_ENTITY}),
a fintech platform offering FD-backed RuPay credit cards in India.

The user has asked a question that isn't covered in our FAQ.
Please provide a helpful response based on your general knowledge,
while making it clear you're providing general information.
Suggest contacting {COMPANY_NAME} support for specific policy questions."""),
        ("human", "{query}")
    ])

    chain = prompt | get_llm()
    response = chain.invoke({"query": query})

    return {
        **state,
        "generation": response.content,
        "confidence": 0.0,
        "context_used": 0
    }


# Conditional edge: Route based on document relevance
def route_after_grading(state: GraphState) -> str:
    """Decide whether to use RAG or fallback based on grading."""
    if state["source"] == "faq":
        return "generate_rag"
    else:
        return "generate_fallback"


# ============== Build LangGraph Workflow ==============

def build_rag_graph() -> StateGraph:
    """Build the LangGraph RAG workflow."""

    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("grade", grade_documents)
    workflow.add_node("generate_rag", generate_rag_response)
    workflow.add_node("generate_fallback", generate_fallback_response)

    # Add edges
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade")

    # Conditional routing after grading
    workflow.add_conditional_edges(
        "grade",
        route_after_grading,
        {
            "generate_rag": "generate_rag",
            "generate_fallback": "generate_fallback"
        }
    )

    # Both generation nodes lead to END
    workflow.add_edge("generate_rag", END)
    workflow.add_edge("generate_fallback", END)

    return workflow.compile()


# ============== RAG Engine Class ==============

class RAGEngine:
    """Main RAG Engine using LangGraph."""

    def __init__(self):
        self.graph = build_rag_graph()
        self.vector_store = get_vector_store()
        print("LangGraph RAG workflow initialized")

    def add_documents(self, documents: List[str]):
        """Add documents to the vector store."""
        self.vector_store.add_documents(documents)

    def get_response(self, query: str) -> Dict[str, Any]:
        """Get response using the LangGraph workflow."""

        # Initial state
        initial_state: GraphState = {
            "query": query,
            "documents": [],
            "generation": "",
            "source": "",
            "confidence": 0.0,
            "context_used": 0
        }

        # Run the graph
        try:
            result = self.graph.invoke(initial_state)

            return {
                "answer": result["generation"],
                "source": result["source"],
                "confidence": result["confidence"],
                "context_used": result["context_used"]
            }
        except Exception as e:
            print(f"Error in LangGraph workflow: {e}")
            return {
                "answer": f"I apologize, but I encountered an error. Please ensure Ollama is running with the {OLLAMA_MODEL} model.",
                "source": "error",
                "confidence": 0.0,
                "context_used": 0
            }

    def is_ready(self) -> bool:
        """Check if the RAG engine is ready."""
        return self.vector_store.index is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        stats = self.vector_store.get_stats()
        stats["llm_model"] = OLLAMA_MODEL
        stats["workflow"] = "LangGraph"
        return stats


# Singleton instance
_rag_engine = None


def get_rag_engine() -> RAGEngine:
    """Get or create the RAG engine singleton."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine


# ============== Testing ==============

if __name__ == "__main__":
    from pdf_processor import process_pdf

    engine = get_rag_engine()

    # Process and add PDF if index is empty
    if engine.vector_store.index.ntotal == 0:
        pdf_path = "Novio_Complete_FAQ_Guide.pdf"
        if os.path.exists(pdf_path):
            chunks = process_pdf(pdf_path)
            engine.add_documents(chunks)
        else:
            print(f"PDF not found: {pdf_path}")
            sample_docs = [
                "Novio offers FD-backed RuPay credit cards. You need a minimum FD of Rs. 10,000 to get started.",
                "To create a Novio account, download the app, enter your mobile number, and complete KYC verification.",
                "Novio cards can be used for UPI payments, online shopping, and at any merchant that accepts RuPay cards."
            ]
            engine.add_documents(sample_docs)

    print(f"\nEngine stats: {engine.get_stats()}")

    # Test query
    test_query = "How do I create an account?"
    print(f"\nTest query: {test_query}")
    response = engine.get_response(test_query)
    print(f"Response: {response}")
