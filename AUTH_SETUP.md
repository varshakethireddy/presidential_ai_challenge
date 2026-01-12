# Authentication & Database Setup

## What Changed

Your Juno Teen Coach app now has:
- **User authentication** (login/signup)
- **SQLite database** to store user data
- **Persistent data** across sessions
- **Individual user accounts** with separate data

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the app:**
```bash
streamlit run app.py
```

3. **Create an account:**
   - Click "Sign Up"
   - Choose a username and password (min 6 characters)
   - Log in with your new credentials

## Database Structure

### Tables:
- **users**: User accounts (username, password, email)
- **chat_sessions**: All chat messages with emotion data
- **journal_entries**: Journal entries with AI prompts

### Database File:
- `juno_data.db` (created automatically in project root)

## Migration (Optional)

If you have existing data in JSONL files:

```bash
python migrate_data.py
```

This creates a "migration_user" account with all your old data.
- Username: `migration_user`
- Password: `changeme123`

## Features

✅ **Secure authentication** with bcrypt password hashing
✅ **Separate data** for each user
✅ **Persistent chat history** (no more resets!)
✅ **Timeline tracks** all emotions across sessions
✅ **Journal entries** saved per user
✅ **Logout** button in sidebar

## How It Works

1. **Login required**: App shows login page first
2. **Database storage**: All messages/journal entries saved to SQLite
3. **User isolation**: Each user only sees their own data
4. **Session persistence**: Chat history loads when you log in

## Files Created

- `database.py` - Database models and setup
- `auth.py` - Login/signup page and authentication
- `db_utils.py` - Database operations (save/load)
- `migrate_data.py` - Optional migration script
- `juno_data.db` - SQLite database (auto-created)

## Technical Details

- **ORM**: SQLAlchemy
- **Password hashing**: bcrypt
- **Database**: SQLite (can switch to PostgreSQL later)
- **Session management**: Streamlit session state + database

## Next Steps

You can now:
- Create multiple user accounts
- Test with different users
- Each user has their own timeline and journal
- Data persists across browser sessions
