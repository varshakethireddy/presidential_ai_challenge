"""Database utility functions for chat and journal operations"""
from database import ChatSession, JournalEntry, get_db
from datetime import datetime

def save_chat_message(user_id: int, session_id: str, role: str, content: str, 
                     intent: str = None, tone: str = None,
                     intent_confidence: float = None, tone_confidence: float = None):
    """Save a chat message to the database"""
    db = get_db()
    try:
        message = ChatSession(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            intent=intent,
            tone=tone,
            intent_confidence=intent_confidence,
            tone_confidence=tone_confidence,
            timestamp=datetime.utcnow()
        )
        db.add(message)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error saving chat message: {e}")
    finally:
        db.close()

def load_chat_messages(user_id: int, session_id: str):
    """Load chat messages for a specific user session"""
    db = get_db()
    try:
        messages = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.session_id == session_id
        ).order_by(ChatSession.timestamp).all()
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "intent": msg.intent,
                "tone": msg.tone,
                "intent_confidence": msg.intent_confidence,
                "tone_confidence": msg.tone_confidence,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]
    finally:
        db.close()

def get_user_chat_history(user_id: int):
    """Get all chat sessions for a user (for timeline)"""
    db = get_db()
    try:
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.intent.isnot(None)
        ).order_by(ChatSession.timestamp).all()
        
        return [
            {
                "session_id": session.session_id,
                "intent": session.intent,
                "tone": session.tone,
                "ts_utc": session.timestamp.isoformat()
            }
            for session in sessions
        ]
    finally:
        db.close()

def get_latest_chat_emotion(user_id: int):
    """Get the most recent emotion data for a user"""
    db = get_db()
    try:
        recent_messages = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.intent.isnot(None)
        ).order_by(ChatSession.timestamp.desc()).limit(3).all()
        
        if not recent_messages:
            return None
        
        recent_messages.reverse()  # Oldest to newest
        
        return {
            "recent_emotions": [
                {
                    "intent": msg.intent,
                    "tone": msg.tone
                } for msg in recent_messages
            ],
            "latest_intent": recent_messages[-1].intent,
            "latest_tone": recent_messages[-1].tone
        }
    finally:
        db.close()

def get_recent_user_messages(user_id: int, limit: int = 6):
    """Get recent user messages for context"""
    db = get_db()
    try:
        messages = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.role == "user"
        ).order_by(ChatSession.timestamp.desc()).limit(limit).all()
        
        messages.reverse()  # Oldest to newest
        
        user_messages = []
        for msg in messages:
            content = msg.content
            if len(content) > 200:
                content = content[:200] + "..."
            user_messages.append(content)
        
        return user_messages
    finally:
        db.close()

def save_journal_entry(user_id: int, session_id: str, content: str, ai_prompt: str = None):
    """Save a journal entry to the database"""
    db = get_db()
    try:
        entry = JournalEntry(
            user_id=user_id,
            session_id=session_id,
            content=content,
            ai_prompt=ai_prompt,
            timestamp=datetime.utcnow()
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error saving journal entry: {e}")
    finally:
        db.close()

def load_journal_entries(user_id: int):
    """Load all journal entries for a user"""
    db = get_db()
    try:
        entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id
        ).order_by(JournalEntry.timestamp.desc()).all()
        
        return [
            {
                "content": entry.content,
                "ai_prompt": entry.ai_prompt,
                "timestamp": entry.timestamp.isoformat(),
                "session_id": entry.session_id
            }
            for entry in entries
        ]
    finally:
        db.close()
