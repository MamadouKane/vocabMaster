"""
Login and Registration Page for VocabMaster
"""
import streamlit as st
import re
import time
from utils.firebase_auth import FirebaseAuth, init_auth_session, login_user, is_authenticated, current_user

# Page configuration
st.set_page_config(
    page_title="Connexion - VocabMaster",
    page_icon="🔐",
    layout="centered"
)

# Initialize authentication
init_auth_session()
auth = FirebaseAuth()

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Le mot de passe doit contenir au moins 6 caractères"
    return True, ""

def main():
    # Custom CSS for login page
    st.markdown("""
    <style>
    .login-header {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
    }
    .auth-form {
        background: #ffffff;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    .tab-content {
        padding: 1.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check if already authenticated
    if is_authenticated():
        username = getattr(st.session_state, 'username', None)
        if username:
            st.success(f"You are welcome : {username}")
        else:
            st.success(f"You are welcome : {st.session_state.user_email}")
        if st.button("🏠 Aller à l'accueil", type="primary"):
            st.switch_page("app.py")
        
        # Display current user information
        current_user()
        return
    
    # Header
    st.markdown("""
    <div class="login-header">
        <h1>🔐 VocabMaster</h1>
        <p>Connectez-vous pour accéder à votre dictionnaire personnel</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auth form container
    st.markdown('<div class="auth-form">', unsafe_allow_html=True)
    
    # Tabs for login and registration
    tab1, tab2 = st.tabs(["🔑 Connexion", "📝 Créer un compte"])
    
    with tab1:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.markdown("### Connectez-vous à votre compte")
        
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="votre@email.com")
            password = st.text_input("🔒 Mot de passe", type="password")
            
            col1, col2 = st.columns([1, 1], gap="large")
            with col1:
                submit_login = st.form_submit_button("🔑 Se connecter", type="primary", use_container_width=True)
            with col2:
                forgot_password = st.form_submit_button(
                    "❓ Mot de passe oublié?",
                    use_container_width=True,
                    help="Réinitialiser votre mot de passe",type="secondary"
                )
            
            if submit_login:
                if not email or not password:
                    st.error("Veuillez remplir tous les champs")
                elif not validate_email(email):
                    st.error("Format d'email invalide")
                else:
                    with st.spinner("Connexion en cours..."):
                        result = auth.sign_in_with_email(email, password)
                        
                        if result['success']:
                            login_user(result)
                            st.success("Connexion réussie!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Erreur de connexion: {result['error']}")
            
            if forgot_password:
                if not email:
                    st.error("Veuillez entrer votre email d'abord")
                elif not validate_email(email):
                    st.error("Format d'email invalide")
                else:
                    with st.spinner("Envoi de l'email de réinitialisation..."):
                        result = auth.send_password_reset(email)
                        if result['success']:
                            st.success("Email de réinitialisation envoyé!")
                        else:
                            st.error(f"Erreur: {result['error']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        st.markdown("### Créer un nouveau compte")
        
        with st.form("register_form"):
            reg_username = st.text_input("👤 Nom d'utilisateur", placeholder="votre pseudo", key="reg_username")
            reg_email = st.text_input("📧 Email", placeholder="votre@email.com", key="reg_email")
            reg_password = st.text_input("🔒 Mot de passe", type="password", key="reg_password")
            reg_confirm_password = st.text_input("🔒 Confirmer le mot de passe", type="password", key="reg_confirm")
            
            
            # Centrer le bouton avec Streamlit columns
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submit_register = st.form_submit_button("📝 Créer le compte", type="primary", use_container_width=True)
            
            if submit_register:
                if not reg_username or not reg_email or not reg_password or not reg_confirm_password:
                    st.error("Veuillez remplir tous les champs")
                elif not validate_email(reg_email):
                    st.error("Format d'email invalide")
                elif reg_password != reg_confirm_password:
                    st.error("Les mots de passe ne correspondent pas")
                else:
                    is_valid, error_msg = validate_password(reg_password)
                    if not is_valid:
                        st.error(error_msg)
                    else:
                        with st.spinner("Création du compte..."):
                            result = auth.sign_up_with_email(reg_email, reg_password, username=reg_username)
                            
                            if result['success']:
                                login_user(result)
                                st.success("Compte créé avec succès!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Erreur lors de la création: {result['error']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Information section
    st.markdown("---")
    st.markdown("### 🔒 Pourquoi s'authentifier?")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🛡️ Sécurité de vos données**
        - Vos mots et statistiques sont protégés
        - Synchronisation sur tous vos appareils
        - Sauvegarde automatique dans le cloud
        """)
    
    with col2:
        st.markdown("""
        **⚡ Fonctionnalités personnalisées**
        - Dictionnaire personnel sécurisé
        - Statistiques d'apprentissage
        - Génération de contenu avec l'IA
        """)

if __name__ == "__main__":
    main()