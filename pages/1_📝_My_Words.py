import streamlit as st
import pandas as pd
from utils.firebase_simple_config import FirebaseSimpleManager
from utils.audio_service import play_audio_button, create_content_with_audio
from utils.firebase_auth import init_auth_session, is_authenticated, get_current_user, logout_user, current_user


# Page configuration
st.set_page_config(
    page_title="My Words - VocabMaster",
    page_icon="📝",
    layout="wide"
)

# Initialize authentication
init_auth_session()

# Check authentication
if not is_authenticated():
    st.warning("Vous devez vous connecter pour voir vos mots.")
    if st.button("🔑 Se connecter", type="primary"):
        st.switch_page("pages/0_🔐_Login.py")
    st.stop()

# Get current user information
current_user()

# Initialize Firebase
@st.cache_resource
def init_firebase():
    return FirebaseSimpleManager()

firebase_manager = init_firebase()

def main():
    st.title("📝 My Words - Mes Mots")
    st.markdown("Voici tous vos mots sauvegardés avec leurs détails")
    
    # Get all words from database
    try:
        words = firebase_manager.get_all_words()
        
        if not words:
            st.info("Aucun mot enregistré pour le moment. Allez sur la page d'accueil pour ajouter des mots!")
            # st.markdown("👉 [Retour à l'accueil](../)")
            if st.button("🏠 Aller à l'accueil", type="primary"):
                st.switch_page("app.py")
            return
        
        st.success(f"📊 Total: {len(words)} mots enregistrés")
        
        # Create search functionality
        search_term = st.text_input("🔍 Rechercher un mot", placeholder="Tapez pour filtrer...")
        
        # Filter words based on search
        if search_term:
            filtered_words = [word for word in words if search_term.lower() in word.get('word', '').lower() 
                            or search_term.lower() in word.get('translation', '').lower()]
        else:
            filtered_words = words
        
        if not filtered_words:
            st.warning(f"Aucun mot trouvé pour '{search_term}'")
            return
        
        # Display words in a table format
        st.markdown("### 📋 Liste des mots")
        
        # Create DataFrame for better display
        df_data = []
        for word in filtered_words:
            df_data.append({
                'Mot': word.get('word', ''),
                'Traduction': word.get('translation', ''),
                'Définition': word.get('definition', '')[:80] + '...' if len(word.get('definition', '')) > 80 else word.get('definition', '')
            })
        
        df = pd.DataFrame(df_data)
        
        # Display table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Mot": st.column_config.TextColumn("Mot anglais", width="medium"),
                "Traduction": st.column_config.TextColumn("Traduction française", width="medium"), 
                "Définition": st.column_config.TextColumn("Définition (aperçu)", width="large")
            }
        )
        
        # Word details section
        st.markdown("---")
        st.markdown("### 🔍 Détails des mots")
        st.markdown("Cliquez sur un mot ci-dessous pour voir tous ses détails:")
        
        # Create expandable sections for each word
        for i, word in enumerate(filtered_words):
            with st.expander(f"📚 {word.get('word', '')} - {word.get('translation', '')}", expanded=False):
                
                # Create columns for better layout
                col1, col2 = st.columns([3, 1])
                
                # Word details with inline audio
                create_content_with_audio(
                    f"**🔤 Mot:** {word.get('word', '')}", 
                    word.get('word', ''), 
                    f"word_detail_{i}_{word.get('word')}",
                    lang='en',
                    content_type="markdown"
                )
                
                create_content_with_audio(
                    f"**🇫🇷 Signification (FR):** {word.get('translation', '')}", 
                    word.get('translation', ''), 
                    f"trans_detail_{i}_{word.get('word')}",
                    lang='fr',
                    content_type="markdown"
                )
                
                create_content_with_audio(
                    f"**📖 Définition (EN):** {word.get('definition', '')}", 
                    word.get('definition', ''), 
                    f"def_detail_{i}_{word.get('word')}",
                    lang='en',
                    content_type="markdown"
                )
                
                # Examples
                if word.get('example1'):
                    create_content_with_audio(
                        f"**💡 Exemple 1:** {word.get('example1')}", 
                        word.get('example1'), 
                        f"ex1_detail_{i}_{word.get('word')}",
                        lang='en',
                        content_type="markdown"
                    )
                
                if word.get('example2'):
                    create_content_with_audio(
                        f"**💡 Exemple 2:** {word.get('example2')}", 
                        word.get('example2'), 
                        f"ex2_detail_{i}_{word.get('word')}",
                        lang='en',
                        content_type="markdown"
                    )
                
                # # Creation date
                # if word.get('created_at'):
                #     st.markdown(f"**📅 Ajouté le:** {word.get('created_at').strftime('%d/%m/%Y à %H:%M')}")
        
        # Quick actions
        st.markdown("---")
        st.markdown("### ⚡ Actions rapides")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎮 Jouer au Quiz", type="primary", use_container_width=True):
                if len(words) >= 15:
                    st.switch_page("pages/2_🎮_Game.py")
                else:
                    st.warning(f"Il vous faut au moins 15 mots pour jouer. Vous en avez {len(words)}.")
        
        with col2:
            if st.button("📊 Voir les Statistiques", use_container_width=True):
                st.switch_page("pages/3_📊_Stats.py")

        with col3:
            if st.button("🏠 Retour Accueil", use_container_width=True):
                st.switch_page("app.py")
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des mots: {str(e)}")
        st.markdown("Veuillez vérifier votre connexion et réessayer.")

if __name__ == "__main__":
    main()
