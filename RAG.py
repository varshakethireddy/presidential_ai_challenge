from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any
import os
from docx import Document
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Cache for loaded documents
_documents_cache = None
_vectorizer_cache = None
_tfidf_matrix_cache = None

def load_cards(path: str = "data/skill_cards.json") -> List[Dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def load_document(file_path: str) -> str:
    """Load text content from PDF or DOCX file"""
    try:
        if file_path.endswith('.pdf'):
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif file_path.endswith('.docx'):
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return ""
    return ""

def load_all_documents(data_dir: str = "data/Data sets") -> List[Dict[str, Any]]:
    """Load all documents from the data directory"""
    global _documents_cache
    
    if _documents_cache is not None:
        return _documents_cache
    
    documents = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        return documents
    
    for file_path in data_path.glob("*"):
        if file_path.suffix in ['.pdf', '.docx', '.txt']:
            content = load_document(str(file_path))
            if content.strip():
                documents.append({
                    "title": file_path.stem,
                    "content": content,
                    "path": str(file_path)
                })
    
    _documents_cache = documents
    return documents

def build_document_index(documents: List[Dict[str, Any]]):
    """Build TF-IDF index for semantic search"""
    global _vectorizer_cache, _tfidf_matrix_cache
    
    if _vectorizer_cache is not None and _tfidf_matrix_cache is not None:
        return _vectorizer_cache, _tfidf_matrix_cache
    
    if not documents:
        return None, None
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words='english',
        ngram_range=(1, 2)
    )
    
    # Build document corpus
    corpus = [doc["content"] for doc in documents]
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    _vectorizer_cache = vectorizer
    _tfidf_matrix_cache = tfidf_matrix
    
    return vectorizer, tfidf_matrix

def search_documents(query: str, intent: str = None, k: int = 3) -> List[Dict[str, Any]]:
    """Search documents using semantic similarity"""
    documents = load_all_documents()
    
    if not documents:
        return []
    
    vectorizer, tfidf_matrix = build_document_index(documents)
    
    if vectorizer is None:
        return []
    
    # Expand query with related terms based on intent
    intent_keywords = {
        "stress": "stress anxiety worried nervous pressure overwhelmed",
        "test_anxiety": "test exam study school grade performance academic",
        "social_anxiety": "social friends peer judgment embarrassed shy awkward",
        "sadness": "sad depressed down lonely isolated unhappy",
        "anger": "angry mad frustrated annoyed irritated",
        "loneliness": "lonely alone isolated friendless disconnected",
        "grief": "grief loss death dying mourning sad",
        "panic": "panic attack fear terror heart racing breathing",
        "overwhelmed": "overwhelmed too much can't cope drowning pressure",
        "fear": "scared afraid frightened worried anxious nervous",
        "worry": "worried worrying anxious concern stress",
        "frustration": "frustrated annoyed irritated stuck blocked",
        "tired": "tired exhausted fatigue drained sleep rest",
        "bored": "bored boring nothing dull uninterested",
        "self_harm": "self harm cutting hurt injury pain",
        "crisis": "crisis emergency danger help now urgent"
    }
    
    # Build enhanced query
    search_terms = [query]
    if intent and intent in intent_keywords:
        search_terms.append(intent_keywords[intent])
    
    search_query = " ".join(search_terms)
    
    # Transform query to TF-IDF vector
    query_vector = vectorizer.transform([search_query])
    
    # Calculate cosine similarity
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    
    # Get top k documents with better scoring
    top_indices = np.argsort(similarities)[-k:][::-1]
    
    results = []
    for idx in top_indices:
        if similarities[idx] > 0.03:  # Lower threshold to include more relevant docs
            doc = documents[idx].copy()
            doc["similarity"] = float(similarities[idx])
            
            # Extract most relevant section (around 800 chars for better context)
            content = doc["content"]
            
            # Try to find the most relevant paragraph
            paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
            
            if paragraphs:
                # Score paragraphs by keyword relevance
                para_scores = []
                query_words = set(search_query.lower().split())
                
                for para in paragraphs:
                    para_lower = para.lower()
                    score = sum(1 for word in query_words if word in para_lower)
                    para_scores.append(score)
                
                # Get best paragraphs
                if max(para_scores) > 0:
                    best_idx = para_scores.index(max(para_scores))
                    # Include best paragraph and neighboring ones for context
                    start_idx = max(0, best_idx - 1)
                    end_idx = min(len(paragraphs), best_idx + 2)
                    excerpt = "\n\n".join(paragraphs[start_idx:end_idx])
                else:
                    excerpt = "\n\n".join(paragraphs[:2])
            else:
                excerpt = content[:800]
            
            # Truncate if still too long
            if len(excerpt) > 1200:
                excerpt = excerpt[:1200] + "..."
            
            doc["excerpt"] = excerpt
            results.append(doc)
    
    return results

def retrieve_cards(cards: List[Dict[str, Any]], intent: str, k: int = 2) -> List[Dict[str, Any]]:
    """Retrieve skill cards by intent (original function for backwards compatibility)"""
    matches = [c for c in cards if intent in c.get("tags", [])]
    return matches[:k] if matches else cards[:k]

def retrieve_combined_context(cards: List[Dict[str, Any]], user_message: str, intent: str, k_cards: int = 2, k_docs: int = 2) -> Dict[str, Any]:
    """Retrieve both skill cards and relevant documents"""
    # Get skill cards
    skill_cards = retrieve_cards(cards, intent, k=k_cards)
    
    # Get relevant documents
    relevant_docs = search_documents(user_message, intent=intent, k=k_docs)
    
    return {
        "skill_cards": skill_cards,
        "documents": relevant_docs
    }