"""
Novio AI Assistant - FastAPI Backend
Main application server with chat API endpoints
"""

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from rag_engine import get_rag_engine
from pdf_processor import process_pdf

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Novio AI Assistant",
    description="RAG-based customer support chatbot for Novio",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Get company info from env
COMPANY_NAME = os.getenv("COMPANY_NAME", "Novio")


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    source: str
    confidence: float
    context_used: int


@app.on_event("startup")
async def startup_event():
    """Initialize RAG engine on startup."""
    print("Initializing Novio AI Assistant...")

    # Get RAG engine
    engine = get_rag_engine()

    # Process PDF if index is empty
    if engine.vector_store.index.ntotal == 0:
        pdf_path = "Novio_Complete_FAQ_Guide.pdf"
        if os.path.exists(pdf_path):
            print(f"Processing FAQ document: {pdf_path}")
            chunks = process_pdf(pdf_path)
            engine.add_documents(chunks)
            print(f"Indexed {len(chunks)} document chunks")
        else:
            print(f"Warning: FAQ PDF not found at {pdf_path}")
            print("The assistant will use general knowledge only.")
            # Add some sample data for demo purposes
            sample_docs = [
                "Novio offers FD-backed RuPay credit cards. You need a minimum Fixed Deposit of Rs. 10,000 to get started with Novio card.",
                "To create a Novio account, download the Novio app from Play Store or App Store, enter your mobile number, verify with OTP, and complete KYC verification with your PAN and Aadhaar.",
                "Novio cards can be used for UPI payments, online shopping, EMI transactions, and at any merchant that accepts RuPay cards across India.",
                "The credit limit on your Novio card is up to 100% of your Fixed Deposit amount. Higher FD means higher credit limit.",
                "Novio FD earns competitive interest rates. Your FD continues to earn interest while you use your credit card.",
                "You can pay your Novio credit card bill through UPI, net banking, debit card, or auto-debit from your bank account.",
                "Novio provides instant virtual card after KYC approval. Physical card is delivered within 7-10 business days.",
                "For any issues with your Novio card, contact customer support at support@novio.in or call the helpline number in the app.",
                "Novio card has no annual fee for the first year. Renewal charges may apply based on your usage and FD amount.",
                "You can track your Novio card spending, FD balance, and payment due dates all within the Novio mobile app."
            ]
            engine.add_documents(sample_docs)
            print("Added sample FAQ data for demonstration")

    print(f"RAG Engine ready with {engine.vector_store.index.ntotal} indexed documents")


@app.get("/")
async def home(request: Request):
    """Serve the main chat interface."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "company_name": COMPANY_NAME}
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process chat messages and return AI responses."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        engine = get_rag_engine()
        response = engine.get_response(request.message.strip())

        return ChatResponse(
            answer=response["answer"],
            source=response["source"],
            confidence=response["confidence"],
            context_used=response["context_used"]
        )
    except Exception as e:
        print(f"Error processing chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request. Please try again."
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    engine = get_rag_engine()
    stats = engine.get_stats()

    return JSONResponse({
        "status": "healthy",
        "service": "Novio AI Assistant",
        "rag_engine": {
            "ready": engine.is_ready(),
            "documents_indexed": stats["total_documents"],
            "embedding_model": stats["embedding_model"],
            "llm_model": stats["llm_model"]
        }
    })


@app.get("/api/stats")
async def get_stats():
    """Get RAG engine statistics."""
    engine = get_rag_engine()
    return JSONResponse(engine.get_stats())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
