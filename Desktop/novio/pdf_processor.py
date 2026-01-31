"""
PDF Processor Module for Novio AI Assistant
Handles PDF text extraction and chunking for RAG pipeline
"""

import os
from typing import List
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    reader = PdfReader(pdf_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


def clean_text(text: str) -> str:
    """Clean and preprocess extracted text."""
    # Remove excessive whitespace
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line:
            # Remove multiple spaces
            line = ' '.join(line.split())
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks for better context retrieval."""
    if not text:
        return []

    chunks = []
    sentences = text.replace('\n', ' ').split('. ')

    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Add period back if it was removed
        if not sentence.endswith('.'):
            sentence += '.'

        # Check if adding this sentence would exceed chunk size
        if len(current_chunk) + len(sentence) + 1 <= chunk_size:
            current_chunk += (" " + sentence if current_chunk else sentence)
        else:
            # Save current chunk if not empty
            if current_chunk:
                chunks.append(current_chunk.strip())

            # Start new chunk with overlap from previous chunk
            if chunks and overlap > 0:
                # Get last few characters as overlap
                prev_chunk = chunks[-1]
                overlap_text = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
                current_chunk = overlap_text + " " + sentence
            else:
                current_chunk = sentence

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def process_pdf(pdf_path: str) -> List[str]:
    """Main function to process PDF and return chunks."""
    print(f"Processing PDF: {pdf_path}")

    # Extract text
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(raw_text)} characters from PDF")

    # Clean text
    cleaned_text = clean_text(raw_text)
    print(f"Cleaned text: {len(cleaned_text)} characters")

    # Chunk text
    chunks = chunk_text(cleaned_text)
    print(f"Created {len(chunks)} chunks")

    return chunks


if __name__ == "__main__":
    # Test with the FAQ PDF
    pdf_path = "Novio_Complete_FAQ_Guide.pdf"
    if os.path.exists(pdf_path):
        chunks = process_pdf(pdf_path)
        print(f"\nFirst chunk preview:\n{chunks[0][:200]}..." if chunks else "No chunks created")
    else:
        print(f"PDF not found: {pdf_path}")
