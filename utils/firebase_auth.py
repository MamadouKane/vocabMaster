"""
Firebase Authentication for VocabMaster
Handles user authentication with Google OAuth and email/password
"""
import streamlit as st
import requests
import json
import time
from .env_loader import get_env_var

# Firebase Auth REST API URLs
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts"
FIREBASE_API_KEY = get_env_var('FIREBASE_API_KEY')

class FirebaseAuth:
    def __init__(self):
        self.api_key = FIREBASE_API_KEY
        if not self.api_key:
            st.error("Firebase API Key manquante. Veuillez configurer FIREBASE_API_KEY.")

    def sign_up_with_email(self, email, password, username):
        """Create a new user account with email and password"""
        url = f"{FIREBASE_AUTH_URL}:signUp?key={self.api_key}"
        payload = {
            "email": email,
            "displayName": username,
            "password": password,
            "returnSecureToken": True
        }
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'user_id': data.get('localId'),
                    'email': data.get('email'),
                    'username': data.get('displayName'),
                    'token': data.get('idToken'),
                    'refresh_token': data.get('refreshToken')
                }
            else:
                error_message = data.get('error', {}).get('message', 'Erreur inconnue')
                return {
                    'success': False,
                    'error': self._format_error_message(error_message)
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Erreur de connexion: {str(e)}"
            }
    
    def sign_in_with_email(self, email, password):
        """Sign in existing user with email and password"""
        url = f"{FIREBASE_AUTH_URL}:signInWithPassword?key={self.api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'user_id': data.get('localId'),
                    'username': data.get('displayName'),
                    'email': data.get('email'),
                    'token': data.get('idToken'),
                    'refresh_token': data.get('refreshToken')
                }
            else:
                error_message = data.get('error', {}).get('message', 'Erreur inconnue')
                return {
                    'success': False,
                    'error': self._format_error_message(error_message)
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Erreur de connexion: {str(e)}"
            }
    
    def refresh_token(self, refresh_token):
        """Refresh the authentication token"""
        url = f"https://securetoken.googleapis.com/v1/token?key={self.api_key}"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'token': data.get('id_token'),
                    'refresh_token': data.get('refresh_token')
                }
            else:
                return {'success': False, 'error': 'Token expired'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def verify_token(self, token):
        """Verify if the token is valid"""
        url = f"{FIREBASE_AUTH_URL}:lookup?key={self.api_key}"
        payload = {"idToken": token}
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            
            if response.status_code == 200:
                users = data.get('users', [])
                if users:
                    user = users[0]
                    return {
                        'success': True,
                        'user_id': user.get('localId'), 
                        'email': user.get('email'),
                        'email_verified': user.get('emailVerified', False),
                        'username': user.get('displayName')
                    }
            return {'success': False, 'error': 'Token invalide'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_password_reset(self, email):
        """Send password reset email"""
        url = f"{FIREBASE_AUTH_URL}:sendOobCode?key={self.api_key}"
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": email
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return {'success': True}
            else:
                data = response.json()
                error_message = data.get('error', {}).get('message', 'Erreur inconnue')
                return {
                    'success': False,
                    'error': self._format_error_message(error_message)
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _format_error_message(self, error_message):
        """Format Firebase error messages in French"""
        error_translations = {
            'EMAIL_EXISTS': 'Cette adresse email est déjà utilisée',
            'EMAIL_NOT_FOUND': 'Aucun compte trouvé avec cette adresse email',
            'INVALID_PASSWORD': 'Mot de passe incorrect',
            'WEAK_PASSWORD': 'Le mot de passe doit contenir au moins 6 caractères',
            'INVALID_EMAIL': 'Adresse email invalide',
            'TOO_MANY_ATTEMPTS_TRY_LATER': 'Trop de tentatives. Réessayez plus tard',
            'USER_DISABLED': 'Ce compte a été désactivé'
        }
        
        return error_translations.get(error_message, error_message)

# Session management functions
def init_auth_session():
    """Initialize authentication session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None 
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'auth_token' not in st.session_state:
        st.session_state.auth_token = None
    if 'refresh_token' not in st.session_state:
        st.session_state.refresh_token = None
    if 'username' not in st.session_state:
        st.session_state.username = None

def login_user(user_data):
    """Set user session data after successful login"""
    st.session_state.authenticated = True
    st.session_state.user_id = user_data.get('user_id')
    st.session_state.user_email = user_data.get('email')
    st.session_state.auth_token = user_data.get('token')
    st.session_state.refresh_token = user_data.get('refresh_token')
    st.session_state.username = user_data.get('username')

def logout_user():
    """Clear user session data"""
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.auth_token = None
    st.session_state.refresh_token = None
    st.session_state.username = None

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def get_current_user():
    """Get current user information"""
    if is_authenticated():
        return {
            'user_id': st.session_state.user_id,
            'username' : st.session_state.username,
            'email': st.session_state.user_email,
            'token': st.session_state.auth_token
        }
    return None

def current_user():
    """Get current user information"""
    # Add logout button in sidebar
    with st.sidebar:
        user = get_current_user()
        if user:
            st.markdown("### 👤 Utilisateur connecté")
            if user.get('username'):
                st.markdown(f"**{user['username']}**")
            else:
                st.markdown(f"**{user['email']}**")
            if st.button("🚪 Se déconnecter", use_container_width=True):
                logout_user()
                st.rerun()

def require_auth():
    """Decorator to require authentication for a page"""
    if not is_authenticated():
        st.warning("Vous devez vous connecter pour accéder à cette page.")
        st.stop()