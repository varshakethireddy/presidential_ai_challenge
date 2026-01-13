"""Database migration script to add confidence columns"""
import sqlite3
import shutil
from datetime import datetime

# Backup the database first
backup_name = f"juno_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
shutil.copy2("juno_data.db", backup_name)
print(f"✓ Created backup: {backup_name}")

# Connect to database
conn = sqlite3.connect("juno_data.db")
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(chat_sessions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "intent_confidence" not in columns:
        print("Adding intent_confidence column...")
        cursor.execute("ALTER TABLE chat_sessions ADD COLUMN intent_confidence REAL")
        print("✓ Added intent_confidence")
    else:
        print("✓ intent_confidence already exists")
    
    if "tone_confidence" not in columns:
        print("Adding tone_confidence column...")
        cursor.execute("ALTER TABLE chat_sessions ADD COLUMN tone_confidence REAL")
        print("✓ Added tone_confidence")
    else:
        print("✓ tone_confidence already exists")
    
    conn.commit()
    print("\n✓ Migration completed successfully!")
    print("The database now supports confidence scores.")
    
except Exception as e:
    print(f"\n✗ Migration failed: {e}")
    conn.rollback()
finally:
    conn.close()
