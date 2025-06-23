import streamlit as st
import json
import os
from utils.env_loader import APP_NAME, DEBUG_MODE
from utils.firebase_simple_config import FirebaseSimpleManager
from utils.ai_service import get_definition_and_examples
from utils.audio_service import play_audio_button, create_content_with_audio
from utils.firebase_auth import init_auth_session, is_authenticated, logout_user, get_current_user, current_user
import time

# Page configuration
st.set_page_config(page_title=APP_NAME,
                   page_icon="📚",
                   layout="wide",
                   initial_sidebar_state="expanded")

# Custom CSS for attractive design
st.markdown("""
    <style>
    .main-header {
    text-align: center;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    .feature-card {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 10px;
    border-left: 4px solid #667eea;
    margin: 1rem auto;
    transition: transform 0.3s ease;
    max-width: 320px;
    }
    .feature-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    margin: 0.5rem auto;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    max-width: 320px;
    }
    .input-section {
    background: #ffffff;
    padding: 2.5rem;
    border-radius: 20px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
    margin: 1rem 0;
    border: 1px solid #e9ecef;
    }
    .how-to-section {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    margin-top: 2rem;
    }
    .step-box {
    background: rgba(255, 255, 255, 0.1);
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem;
    backdrop-filter: blur(10px);
    }
    .stButton > button {
    max-width: 320px;
    width: 100%;
    margin: 0.5rem auto;
    display: block;
    }
    </style>
    """, unsafe_allow_html=True
)

# Initialize authentication
init_auth_session()

# Authentication section
if not is_authenticated():
    
    current_user()
    
    # Hero header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 VocabMaster</h1>
        <h3>Votre compagnon intelligent pour apprendre l'anglais</h3>
        <p>Transformez chaque mot en une leçon complète avec l'IA</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔑 Se connecter | S'inscrire", type="primary", use_container_width=True):
            st.switch_page("pages/0_Login.py")
    
    st.markdown("---")
    # Fonctionnalities 
    st.markdown("""
    <div style="text-align:center; margin-bottom: 2rem;">
        <h2 style="font-weight:700; letter-spacing:1px;">🌟 Fonctionnalités</h2>
    </div>
    <div style="
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 2rem;
        margin-bottom: 2rem;
    ">
        <div class="feature-card" style="
            min-width: 250px;
            max-width: 320px;
            flex: 1 1 250px;
            box-shadow: 0 4px 15px rgba(102,126,234,0.08);
            border-left: 4px solid #667eea;
        ">
            <h4 style="margin-top:0.5rem;">🤖 IA Avancée</h4>
            <h6 style="margin-top:0.5rem;">Entrez un mot ou une expression et l'IA se charge du reste :</h6>
            <ul style="text-align:left; padding-left:1.2em;">
                <li>Définitions automatiques</li>
                <li>Traductions précises</li>
                <li>Exemples contextuels</li>
            </ul>
        </div>
        <div class="feature-card" style="
            min-width: 250px;
            max-width: 320px;
            flex: 1 1 250px;
            box-shadow: 0 4px 15px rgba(102,126,234,0.08);
            border-left: 4px solid #764ba2;
        ">
            <h4 style="margin-top:0.5rem;">🔊 Audio Intégré</h4>
            <ul style="text-align:left; padding-left:1.2em;">
                <li>Prononciation de chaque mot</li>
                <li>Audio pour les exemples</li>
                <li>Interface intuitive</li>
            </ul>
        </div>
        <div class="feature-card" style="
            min-width: 250px;
            max-width: 320px;
            flex: 1 1 250px;
            box-shadow: 0 4px 15px rgba(102,126,234,0.08);
            border-left: 4px solid #f5576c;
        ">
            <h4 style="margin-top:0.5rem;">🎮 Quiz Interactif</h4>
            <ul style="text-align:left; padding-left:1.2em;">
                <li>Deux modes de jeu</li>
                <li>Statistiques détaillées</li>
                <li>Suivi des progrès</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.stop()


# Initialize Firebase
@st.cache_resource
def init_firebase():
    return FirebaseSimpleManager()


firebase_manager = init_firebase()

# Initialize session state
if 'selected_word_details' not in st.session_state:
    st.session_state.selected_word_details = None


def main():
    #  Get current user information and Add logout button in sidebar
    current_user()
    
    # Hero header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 VocabMaster</h1>
        <h3>Votre compagnon intelligent pour apprendre l'anglais</h3>
        <p>Transformez chaque mot en une leçon complète avec l'IA</p>
    </div>
    """, unsafe_allow_html=True)
    # Create two columns for better layout
    _ , col2, _ = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        
        # Word input section with attractive design
        st.markdown("### ✨ Découvrez un nouveau mot")
        st.markdown("Entrez un mot anglais et obtenez instantanément sa définition, traduction et exemples d'usage")
        
        word_input = st.text_input("Mot à apprendre", 
                                   placeholder="Ex: beautiful, adventure, curiosity, serendipity...",
                                   key="word_input",
                                   label_visibility="collapsed")
        
        validate_btn = st.button("🚀 Générer avec l'IA", 
                                 type="primary", 
                                 use_container_width=True)

        # Process word when button is clicked
        if validate_btn and word_input.strip():
            with st.spinner("Génération du contenu en cours..."):
                word_data = get_definition_and_examples(word_input.strip())

                if word_data:
                    st.session_state.current_word_data = word_data
                    st.success("Contenu généré avec succès!")
                else:
                    st.error(
                        "Erreur lors de la génération du contenu. Veuillez réessayer."
                    )


        # Display generated content
        if 'current_word_data' in st.session_state and st.session_state.current_word_data:
            word_data = st.session_state.current_word_data

            st.markdown("---")
            st.markdown("### 📖 Résultats générés")

            # Word section
            create_content_with_audio(
                f"**Mot:** {word_data.get('word', word_input)}",
                word_data.get('word', word_input),
                f"word_{word_data.get('word', word_input)}",
                lang='en',
                content_type="markdown")

            # French translation (no audio)
            if 'translation' in word_data:
                st.markdown(f"**Signification (FR):** {word_data['translation']}")

            # English definition
            if 'definition' in word_data:
                create_content_with_audio(
                    f"**Définition (EN):** {word_data['definition']}",
                    word_data['definition'],
                    f"definition_{word_data.get('word', word_input)}",
                    lang='en',
                    content_type="markdown")

            # Examples
            if 'example1' in word_data:
                create_content_with_audio(
                    f"**Exemple 1:** {word_data['example1']}",
                    word_data['example1'],
                    f"example1_{word_data.get('word', word_input)}",
                    lang='en',
                    content_type="markdown")

            if 'example2' in word_data:
                create_content_with_audio(
                    f"**Exemple 2:** {word_data['example2']}",
                    word_data['example2'],
                    f"example2_{word_data.get('word', word_input)}",
                    lang='en',
                    content_type="markdown")

            # Add to My Words button
            st.markdown("---")
            if st.button("➕ Ajouter dans My Words",
                         type="secondary",
                         use_container_width=True):
                try:
                    # Save to Firebase
                    success = firebase_manager.add_word(word_data)
                    if success:
                        st.success(
                            f"'{word_data.get('word', word_input)}' ajouté à vos mots!"
                        )
                        # Clear current word data
                        del st.session_state.current_word_data
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(
                            "Erreur lors de la sauvegarde. Veuillez réessayer."
                        )
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")

if __name__ == "__main__":
    main()
