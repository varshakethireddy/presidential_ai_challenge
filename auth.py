"""Authentication module for user login and signup"""
import streamlit as st
import bcrypt
import json
from pathlib import Path
from database import User, get_db

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def export_users_to_json():
    """Export all users to a JSON file for easy viewing"""
    db = get_db()
    try:
        users = db.query(User).all()
        users_list = []
        
        for user in users:
            users_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None
            })
        
        # Save to JSON file
        output_file = Path("logs/users.json")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(users_list, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error exporting users: {e}")
        return False
    finally:
        db.close()

def create_user(username: str, password: str, email: str = None) -> tuple[bool, str]:
    """Create a new user account"""
    db = get_db()
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return False, "Username already exists"
        
        # Check if email already exists (if provided)
        if email:
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                return False, "Email already exists"
        
        # Create new user
        password_hash = hash_password(password)
        new_user = User(
            username=username,
            password_hash=password_hash,
            email=email
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Export users to JSON file after creating new user
        export_users_to_json()
        
        return True, "Account created successfully!"
    except Exception as e:
        db.rollback()
        return False, f"Error creating account: {str(e)}"
    finally:
        db.close()

def authenticate_user(username: str, password: str) -> tuple[bool, User | None]:
    """Authenticate a user with username and password"""
    db = get_db()
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return False, None
        
        if verify_password(password, user.password_hash):
            return True, user
        else:
            return False, None
    finally:
        db.close()

def render_auth_page():
    """Render the login/signup page"""
    st.markdown("""
        <style>
        .auth-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background-color: #f8f9fa;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Center the form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #8fc5a3;'>🌟 juno</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6b8e7f; margin-bottom: 10px;'>Your AI companion for emotional well-being</p>", unsafe_allow_html=True)
        
        # Add custom CSS to shift radio buttons to the right
        st.markdown("""
            <style>
            div[role="radiogroup"] {
                margin-left: 2cm;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Toggle between login and signup
        auth_mode = st.radio("", ["Login", "Sign Up"], horizontal=True, label_visibility="collapsed")
        
        st.markdown("---")
        
        if auth_mode == "Sign Up":
            render_signup_form()
        else:
            render_login_form()

def render_login_form():
    """Render the login form"""
    with st.form("login_form", clear_on_submit=False):
        st.markdown("### Welcome Back!")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        submit = st.form_submit_button("Log In", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                success, user = authenticate_user(username, password)
                if success:
                    # Set session state
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = user.id
                    st.session_state["username"] = user.username
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

def render_signup_form():
    """Render the signup form"""
    with st.form("signup_form", clear_on_submit=True):
        st.markdown("### Create Your Account")
        username = st.text_input("Username", key="signup_username", help="Choose a unique username")
        password = st.text_input("Password", type="password", key="signup_password", help="Min 6 characters")
        password_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm")
        
        submit = st.form_submit_button("Sign Up", use_container_width=True)
        
        if submit:
            # Validation
            if not username or not password:
                st.error("Username and password are required")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            elif password != password_confirm:
                st.error("Passwords do not match")
            else:
                success, message = create_user(username, password)
                if success:
                    st.success(message)
                    st.info("Please log in with your new account")
                else:
                    st.error(message)

def logout():
    """Log out the current user"""
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["username"] = None
    st.session_state["session_id"] = None
    st.session_state["messages"] = None  # Clear chat messages
    st.session_state["last_loaded_user_id"] = None  # Clear user tracking
    st.rerun()

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)
