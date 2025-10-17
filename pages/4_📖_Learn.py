import streamlit as st
import json
import re
from utils.firebase_simple_config import FirebaseSimpleManager
from utils.firebase_auth import init_auth_session, is_authenticated, current_user
from utils.ai_service import client, get_definition_and_examples, validate_word_data

# Page configuration
st.set_page_config(
    page_title="Learn - VocabMaster",
    page_icon="📖",
    layout="wide"
)

# Initialize auth
init_auth_session()

# Require authentication
if not is_authenticated():
    st.warning("Vous devez vous connecter pour accéder à la page Learn.")
    if st.button("🔑 Se connecter", type="primary"):
        st.switch_page("pages/0_🔑_Login.py")
    st.stop()

# Show current user and logout
current_user()

# Initialize firebase manager
@st.cache_resource
def init_firebase():
    return FirebaseSimpleManager()

firebase_manager = init_firebase()

# Helper functions
def clean_word_suggestion(text):
    """Clean a single word suggestion from AI response."""
    if not text or not isinstance(text, str):
        return None
    
    # Remove common prefixes and suffixes
    cleaned = re.sub(r'^\s*[\d\-•\*\[\]]+\.?\s*', '', text.strip())
    cleaned = re.sub(r'["\',\[\]]+', '', cleaned)
    cleaned = cleaned.strip()
    
    # Filter out very short or long suggestions
    if len(cleaned) < 2 or len(cleaned) > 50:
        return None
    
    # Filter out common stop words or very basic words
    basic_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    if cleaned.lower() in basic_words:
        return None
        
    return cleaned

def parse_ai_response(text):
    """Parse AI response to extract clean word suggestions."""
    suggestions = []
    
    try:
        # First, try to parse as JSON
        if text.strip().startswith('[') and text.strip().endswith(']'):
            parsed = json.loads(text)
            if isinstance(parsed, list):
                for item in parsed:
                    cleaned = clean_word_suggestion(str(item))
                    if cleaned:
                        suggestions.append(cleaned)
                return suggestions
    except json.JSONDecodeError:
        pass
    
    # Fallback: parse line by line
    lines = text.split('\n')
    for line in lines:
        cleaned = clean_word_suggestion(line)
        if cleaned:
            suggestions.append(cleaned)
    
    # Also try comma-separated values
    if ',' in text and len(suggestions) < 3:
        parts = text.split(',')
        for part in parts:
            cleaned = clean_word_suggestion(part)
            if cleaned:
                suggestions.append(cleaned)
    
    return list(set(suggestions))  # Remove duplicates

def get_existing_words():
    """Get existing words from database safely."""
    try:
        existing_words = firebase_manager.get_all_words()
        if existing_words is None:
            return set()
        return {word.get('word', '').lower().strip() for word in existing_words if word.get('word')}
    except Exception as e:
        st.error(f"Erreur lors de la récupération des mots existants: {str(e)}")
        return set()

def request_ai_suggestions(count=7, level="Any", context="Any"):
    """Request word suggestions from AI with improved error handling."""
    
    # Build context-specific prompts
    level_instructions = {
        "Beginner": "simple, common English words that beginners should know",
        "Intermediate": "intermediate English vocabulary including phrasal verbs and expressions",
        "Advanced": "advanced English vocabulary, idioms, and sophisticated expressions"
    }
    
    context_instructions = {
        "Loisir": "leisure activities, hobbies, sports, entertainment",
        "Voyage": "travel, tourism, transportation, hotels, restaurants",
        "Monde pro": "business, work, meetings, professional communication",
        "Nature": "environment, animals, plants, weather, geography",
        "Nouvelle connaissance": "meeting people, social situations, getting to know someone"
    }
    
    level_text = level_instructions.get(level, "various English words and expressions")
    context_text = f" related to {context_instructions.get(context, 'general topics')}" if context != "Any" else ""
    
    prompt = f"""Generate exactly {count} English words or short expressions for language learners.
    
    Focus on: {level_text}{context_text}
    
    Requirements:
    - Return ONLY a valid JSON array
    - Format: ["word1", "phrase2", "word3", ...]
    - No explanations or extra text
    - Avoid basic words like: hello, yes, no, please, thank you
    - Include a mix of single words and short phrases
    - Make them useful for vocabulary learning
    
    Example: ["serendipity", "break the ice", "procrastinate", "state of the art", "mindset"]"""
    
    try:
        response = client.chat.completions.create(
            model="mistralai/Mistral-Nemo-Instruct-2407",
            messages=[
                {"role": "system", "content": "You are a helpful English vocabulary teacher. Always respond with valid JSON arrays only, no other text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.8,
        )
        
        if not response.choices or not response.choices[0].message:
            return []
            
        content = response.choices[0].message.content.strip()
        suggestions = parse_ai_response(content)
        
        return suggestions[:count]
        
    except Exception as e:
        # Provide fallback suggestions based on context
        fallback_suggestions = {
            "Loisir": ["hobby", "leisure", "entertainment", "pastime", "recreation"],
            "Voyage": ["journey", "destination", "itinerary", "accommodation", "sightseeing"],
            "Monde pro": ["deadline", "meeting", "colleague", "presentation", "workflow"],
            "Nature": ["landscape", "wildlife", "ecosystem", "biodiversity", "climate"],
            "Nouvelle connaissance": ["introduce", "acquaintance", "background", "personality", "connection"]
        }
        
        fallback = fallback_suggestions.get(context, ["vocabulary", "learning", "language", "practice", "improve"])
        st.warning(f"Utilisation de suggestions par défaut en raison d'une erreur IA: {str(e)}")
        return fallback[:count]

def generate_suggestions(count=5, level="Any", context="Any"):
    """Generate suggestions and filter existing words."""
    try:
        # Get existing words
        existing_words = get_existing_words()
        
        # Request more suggestions than needed to account for filtering
        raw_suggestions = request_ai_suggestions(count=count*2, level=level, context=context)
        
        if not raw_suggestions:
            return []
        
        # Filter out existing words
        filtered = []
        for suggestion in raw_suggestions:
            if suggestion.lower().strip() not in existing_words:
                filtered.append(suggestion)
                if len(filtered) >= count:
                    break
        
        return filtered
        
    except Exception as e:
        st.error(f"Erreur lors de la génération des suggestions: {str(e)}")
        return []

def load_word_details(word):
    """Load detailed information for a word."""
    try:
        word_data = get_definition_and_examples(word)
        
        if word_data and validate_word_data(word_data):
            return word_data
        else:
            # Create minimal valid word data
            return {
                'word': word,
                'definition': f"An English word or expression: {word}",
                'translation': f"Mot anglais: {word}",
                'example1': f"I learned the word '{word}' today.",
                'example2': f"The term '{word}' is useful in English."
            }
    except Exception as e:
        st.error(f"Erreur lors du chargement des détails pour '{word}': {str(e)}")
        return None

# Initialize session state
if 'learn_suggestions' not in st.session_state:
    st.session_state.learn_suggestions = []
if 'learn_word_details' not in st.session_state:
    st.session_state.learn_word_details = {}
if 'learn_added_words' not in st.session_state:
    st.session_state.learn_added_words = set()
if 'learn_loading' not in st.session_state:
    st.session_state.learn_loading = False

# Main UI
st.title("📖 Learn - Suggestions IA")
st.markdown("L'IA vous propose des mots et expressions à apprendre. Vous pouvez les ajouter à votre vocabulaire.")

# Controls
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    level = st.selectbox(
        "Niveau de difficulté",
        ["Any", "Beginner", "Intermediate", "Advanced"],
        index=0
    )

with col2:
    context = st.selectbox(
        "Contexte thématique",
        ["Any", "Loisir", "Voyage", "Monde pro", "Nature", "Nouvelle connaissance"],
        index=0
    )

with col3:
    generate_clicked = st.button("🔄 Nouvelles suggestions", use_container_width=True, disabled=st.session_state.learn_loading)

# Handle suggestion generation
if generate_clicked:
    st.session_state.learn_loading = True
    with st.spinner("Génération des suggestions..."):
        try:
            new_suggestions = generate_suggestions(count=5, level=level, context=context)
            
            if new_suggestions:
                st.session_state.learn_suggestions = new_suggestions
                st.session_state.learn_word_details = {}  # Clear cached details
                st.session_state.learn_added_words = set()  # Reset for new batch
                st.success(f"✅ {len(new_suggestions)} nouvelles suggestions générées!")
            else:
                st.warning("⚠️ Aucune nouvelle suggestion trouvée. Tous les mots suggérés sont déjà dans votre vocabulaire.")
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération: {str(e)}")
        finally:
            st.session_state.learn_loading = False
            st.rerun()

# Load initial suggestions if none exist
if not st.session_state.learn_suggestions and not st.session_state.learn_loading:
    st.session_state.learn_loading = True
    with st.spinner("Chargement des suggestions initiales..."):
        try:
            initial_suggestions = generate_suggestions(count=5, level=level, context=context)
            st.session_state.learn_suggestions = initial_suggestions
        except Exception as e:
            st.error(f"Erreur lors du chargement initial: {str(e)}")
        finally:
            st.session_state.learn_loading = False

# Display suggestions
suggestions = st.session_state.learn_suggestions

if not suggestions:
    st.info("🔄 Cliquez sur 'Nouvelles suggestions' pour générer des mots à apprendre.")
else:
    st.markdown(f"### 💡 Suggestions ({len(suggestions)} mots)")
    
    for i, word in enumerate(suggestions):
        with st.expander(f"📝 {word}", expanded=False):
            col_info, col_actions = st.columns([3, 1])
            
            with col_info:
                st.markdown(f"**Mot/Expression:** `{word}`")
                
                # Show details if loaded
                if word in st.session_state.learn_word_details:
                    details = st.session_state.learn_word_details[word]
                    st.markdown(f"**Traduction:** {details.get('translation', 'Non disponible')}")
                    st.markdown(f"**Définition:** {details.get('definition', 'Non disponible')}")
                    st.markdown(f"**Exemple 1:** *{details.get('example1', 'Non disponible')}*")
                    st.markdown(f"**Exemple 2:** *{details.get('example2', 'Non disponible')}*")
                else:
                    st.info("💡 Cliquez sur 'Charger détails' pour voir la définition, traduction et exemples.")
            
            with col_actions:
                # Load details button
                if word not in st.session_state.learn_word_details:
                    if st.button("🔍 Charger détails", key=f"details_{i}"):
                        with st.spinner(f"Chargement de '{word}'..."):
                            details = load_word_details(word)
                            if details:
                                st.session_state.learn_word_details[word] = details
                                st.rerun()
                
                st.markdown("")  # Add some space
                
                # Add word button
                if word in st.session_state.learn_added_words:
                    st.success("✅ Ajouté")
                else:
                    if st.button("➕ Ajouter", key=f"add_{i}", use_container_width=True):
                        # Load details first if not already loaded
                        if word not in st.session_state.learn_word_details:
                            with st.spinner(f"Chargement de '{word}'..."):
                                details = load_word_details(word)
                                if details:
                                    st.session_state.learn_word_details[word] = details
                        
                        # Add to database
                        if word in st.session_state.learn_word_details:
                            word_data = st.session_state.learn_word_details[word]
                            try:
                                success = firebase_manager.add_word(word_data)
                                if success:
                                    st.session_state.learn_added_words.add(word)
                                    st.success(f"✅ '{word}' ajouté à votre vocabulaire!")
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur: Le mot existe peut-être déjà.")
                            except Exception as e:
                                st.error(f"❌ Erreur lors de l'ajout: {str(e)}")
                        else:
                            st.error("❌ Impossible de charger les détails.")

# Navigation footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("🏠 Accueil", use_container_width=True):
        st.switch_page("app.py")

with col2:
    if st.button("📚 Mes mots", use_container_width=True):
        st.switch_page("pages/1_📚_My_Words.py")

with col3:
    if st.button("🎯 Quiz", use_container_width=True):
        st.switch_page("pages/2_🎯_Quiz.py")