"""
Migration script to transfer data from JSONL files to database
Run this once to migrate existing data (optional)
"""
import json
from pathlib import Path
from database import User, ChatSession, JournalEntry, get_db, init_db
from auth import hash_password
from datetime import datetime

def migrate_to_database():
    """Migrate existing JSONL data to database"""
    print("Initializing database...")
    init_db()
    
    db = get_db()
    
    try:
        # Create a default user for existing data
        print("\nCreating default user for migration...")
        existing_user = db.query(User).filter(User.username == "migration_user").first()
        
        if not existing_user:
            user = User(
                username="migration_user",
                password_hash=hash_password("changeme123"),
                email="migration@example.com"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created user: {user.username} (ID: {user.id})")
        else:
            user = existing_user
            print(f"Using existing user: {user.username} (ID: {user.id})")
        
        # Migrate chat sessions
        chat_log_path = Path("logs/chat_sessions.jsonl")
        if chat_log_path.exists():
            print(f"\nMigrating chat sessions from {chat_log_path}...")
            chat_count = 0
            
            with open(chat_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        
                        # Note: Original JSONL doesn't store individual messages
                        # This is metadata only - actual messages will be fresh
                        session = ChatSession(
                            user_id=user.id,
                            session_id=entry.get("session_id", "unknown"),
                            role="assistant",  # Placeholder
                            content="[Migrated session metadata]",
                            intent=entry.get("intent"),
                            tone=entry.get("tone"),
                            timestamp=datetime.fromisoformat(entry.get("ts_utc", datetime.utcnow().isoformat()))
                        )
                        db.add(session)
                        chat_count += 1
            
            db.commit()
            print(f"Migrated {chat_count} chat session entries")
        else:
            print(f"No chat sessions file found at {chat_log_path}")
        
        # Migrate journal entries
        journal_log_path = Path("logs/journal_entries.jsonl")
        if journal_log_path.exists():
            print(f"\nMigrating journal entries from {journal_log_path}...")
            journal_count = 0
            
            with open(journal_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        
                        journal = JournalEntry(
                            user_id=user.id,
                            session_id=entry.get("session_id", "unknown"),
                            content=entry.get("content", ""),
                            ai_prompt=entry.get("ai_prompt"),
                            timestamp=datetime.fromisoformat(entry.get("timestamp", datetime.utcnow().isoformat()))
                        )
                        db.add(journal)
                        journal_count += 1
            
            db.commit()
            print(f"Migrated {journal_count} journal entries")
        else:
            print(f"No journal entries file found at {journal_log_path}")
        
        print("\n✅ Migration complete!")
        print(f"\nDefault credentials:")
        print(f"  Username: migration_user")
        print(f"  Password: changeme123")
        print(f"\nYou can now:")
        print(f"  1. Log in with these credentials to see migrated data")
        print(f"  2. Create a new account for fresh data")
        print(f"  3. Change the password after logging in")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_to_database()
