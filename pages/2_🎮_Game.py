import streamlit as st
import random
from utils.firebase_simple_config import FirebaseSimpleManager
from utils.audio_service import play_audio_button, create_content_with_audio
from utils.firebase_auth import init_auth_session, is_authenticated, get_current_user, logout_user, current_user

# Page configuration
st.set_page_config(
    page_title="Game - VocabMaster",
    page_icon="🎮",
    layout="wide"
)

# Initialize authentication
init_auth_session()

# Check authentication
if not is_authenticated():
    st.warning("Vous devez vous connecter pour jouer au quiz.")
    if st.button("🔑 Se connecter", type="primary"):
        st.switch_page("pages/0_🔐_Login.py")
    st.stop()

# Initialize Firebase
@st.cache_resource
def init_firebase():
    return FirebaseSimpleManager()

firebase_manager = init_firebase()

# Initialize session state
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
if 'game_mode' not in st.session_state:
    st.session_state.game_mode = None
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'quiz_words' not in st.session_state:
    st.session_state.quiz_words = []
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = []
if 'game_completed' not in st.session_state:
    st.session_state.game_completed = False

def generate_wrong_answers(correct_answer, all_words, mode="translation"):
    """Generate 3 wrong answers for multiple choice"""
    if mode == "translation":
        # For translation mode - get wrong translations
        all_answers = [word.get('translation', '') for word in all_words if word.get('translation', '') != correct_answer]
        
        if len(all_answers) >= 3:
            wrong_answers = random.sample(all_answers, 3)
        else:
            # Generic wrong translations
            generic_wrong = [
                "Un animal domestique",
                "Un objet de cuisine",
                "Une couleur vive",
                "Un moyen de transport",
                "Un sentiment positif",
                "Une action quotidienne",
                "Un élément naturel",
                "Une partie du corps"
            ]
            wrong_answers = all_answers + random.sample(generic_wrong, 3 - len(all_answers))
    
    elif mode == "definition":
        # For definition mode - get wrong definitions
        all_answers = [word.get('definition', '') for word in all_words if word.get('definition', '') != correct_answer and word.get('definition', '')]
        
        if len(all_answers) >= 3:
            wrong_answers = random.sample(all_answers, 3)
        else:
            # Generic wrong definitions
            generic_wrong = [
                "A feeling of great pleasure and happiness",
                "The action of traveling in or through an unfamiliar area",
                "A person whom one knows and with whom one has a bond",
                "The ability to do something that frightens one",
                "The quality of having experience, knowledge, and good judgment",
                "A large naturally occurring community of flora and fauna",
                "The practice of being or tendency to be positive or optimistic",
                "Something that is remembered from the past"
            ]
            wrong_answers = all_answers + random.sample(generic_wrong, min(3 - len(all_answers), len(generic_wrong)))
    
    return wrong_answers[:3]

def start_new_game(mode="translation"):
    """Initialize a new game with selected mode"""
    try:
        # Get all words
        all_words = firebase_manager.get_all_words()
        
        if len(all_words) < 15:
            st.error(f"Il vous faut au moins 15 mots pour jouer. Vous en avez {len(all_words)}.")
            return False
        
        # Select 10 random words for the quiz
        quiz_words = random.sample(all_words, 10)
        
        # Prepare quiz data with multiple choices based on mode
        quiz_data = []
        for word in quiz_words:
            if mode == "translation":
                correct_answer = word.get('translation', '')
                question_text = word.get('word', '')
            else:  # definition mode
                correct_answer = word.get('definition', '')
                question_text = word.get('word', '')
            
            wrong_answers = generate_wrong_answers(correct_answer, all_words, mode)
            
            # Create choices list and shuffle
            choices = [correct_answer] + wrong_answers
            random.shuffle(choices)
            
            quiz_data.append({
                'word': word.get('word', ''),
                'question_text': question_text,
                'correct_answer': correct_answer,
                'choices': choices,
                'definition': word.get('definition', ''),
                'translation': word.get('translation', ''),
                'example1': word.get('example1', ''),
                'example2': word.get('example2', ''),
                'mode': mode
            })
        
        # Reset game state
        st.session_state.quiz_words = quiz_data
        st.session_state.current_question = 0
        st.session_state.score = 0
        st.session_state.user_answers = []
        st.session_state.game_active = True
        st.session_state.game_completed = False
        st.session_state.game_mode = mode
        
        return True
        
    except Exception as e:
        st.error(f"Erreur lors de l'initialisation du jeu: {str(e)}")
        return False

def submit_answer(selected_choice):
    """Process the submitted answer"""
    current_word = st.session_state.quiz_words[st.session_state.current_question]
    is_correct = selected_choice == current_word['correct_answer']
    
    # Record the answer
    st.session_state.user_answers.append({
        'word': current_word['word'],
        'selected': selected_choice,
        'correct': current_word['correct_answer'],
        'is_correct': is_correct
    })
    
    # Update score
    if is_correct:
        st.session_state.score += 1
    
    # Move to next question or finish game
    if st.session_state.current_question < len(st.session_state.quiz_words) - 1:
        st.session_state.current_question += 1
    else:
        # Game completed
        st.session_state.game_completed = True
        st.session_state.game_active = False
        
        # Save score to database
        try:
            firebase_manager.save_game_result(st.session_state.score, len(st.session_state.quiz_words))
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde du score: {str(e)}")

def main():
    st.title("🎮 Game - Quiz de Vocabulaire")

    # display current user info
    current_user()
    
    # Check if user has enough words
    try:
        total_words = firebase_manager.get_total_words_count()
        
        if total_words < 15:
            st.warning(f"⚠️ Il vous faut au moins 15 mots pour jouer au quiz.")
            st.info(f"📊 Vous avez actuellement {total_words} mots enregistrés.")
            st.markdown("👉 Allez sur la page d'accueil pour ajouter plus de mots!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏠 Retour à l'accueil", use_container_width=True):
                    st.switch_page("app.py")
            with col2:
                if st.button("📝 Voir mes mots", use_container_width=True):
                    st.switch_page("pages/1_📝_My_Words.py")
            return
        
        # Game not started - show mode selection and start button
        if not st.session_state.game_active and not st.session_state.game_completed:
            st.markdown("### 🎯 Choisissez votre mode de jeu")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           padding: 1.5rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 1rem;'>
                    <h3>🔤 Find Translation</h3>
                    <p>Trouvez la traduction française du mot anglais</p>
                    <p><strong>Ex:</strong> beautiful → ?</p>
                </div>
                """, unsafe_allow_html=True)
                # Centrer le bouton avec une colonne vide de chaque côté
                btn_col1, btn_col2, btn_col3 = st.columns([2, 3, 1])
                with btn_col2:
                    if st.button("🎮 Jouer à Find Translation", type="primary"):
                        if start_new_game("translation"):
                            st.rerun()
            
            with col2:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                           padding: 1.5rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 1rem;'>
                    <h3>📖 Find Definition</h3>
                    <p>Trouvez la définition anglaise du mot</p>
                    <p><strong>Ex:</strong> beautiful → ?</p>
                </div>
                """, unsafe_allow_html=True)
                btn_col1, btn_col2, btn_col3 = st.columns([2, 3, 1])
                with btn_col2:
                    if st.button("🎮 Jouer à Find Definition", type="primary"):
                        if start_new_game("definition"):
                            st.rerun()
            
            st.markdown("---")
            st.markdown("### 📋 Instructions")
            st.markdown(f"**📚 Mots disponibles:** {total_words}")
            st.markdown("• **Find Translation**: Choisissez la traduction française correcte parmi 4 options")
            st.markdown("• **Find Definition**: Choisissez la définition anglaise correcte parmi 4 options")
            st.markdown("• Chaque partie contient 10 questions")
            st.markdown("• Votre score sera sauvegardé automatiquement")
        
        # Game in progress
        elif st.session_state.game_active and not st.session_state.game_completed:
            current_q = st.session_state.current_question
            total_q = len(st.session_state.quiz_words)
            current_word_data = st.session_state.quiz_words[current_q]
            
            # Progress bar
            progress = (current_q + 1) / total_q
            st.progress(progress, text=f"Question {current_q + 1} sur {total_q}")
            
            # Question
            st.markdown(f"### Question {current_q + 1}/{total_q}")
            
            # Word with audio
            create_content_with_audio(
                f"## 🔤 **{current_word_data['word']}**", 
                current_word_data['word'], 
                f"game_word_{current_q}",
                lang='en',
                content_type="markdown"
            )
            
            # Question text based on game mode
            if st.session_state.game_mode == "translation":
                st.markdown("**Quelle est la signification de ce mot en français ?**")
            else:  # definition mode
                st.markdown("**Quelle est la définition de ce mot en anglais ?**")
            
            # Multiple choice options
            st.markdown("---")
            choices = current_word_data['choices']
            
            # Create radio buttons for choices
            selected_choice = st.radio(
                "Choisissez la bonne réponse:",
                choices,
                key=f"question_{current_q}",
                index=None
            )
            
            # Submit button
            if selected_choice:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("✅ Valider la réponse", type="primary", use_container_width=True):
                        submit_answer(selected_choice)
                        st.rerun()
            
            # Current score
            st.sidebar.markdown(f"### 📊 Score actuel")
            st.sidebar.markdown(f"**{st.session_state.score}/{current_q + 1}** réponses correctes")
            if current_q > 0:
                percentage = (st.session_state.score / (current_q + 1)) * 100
                st.sidebar.markdown(f"**{percentage:.1f}%** de réussite")
        
        # Game completed
        elif st.session_state.game_completed:
            total_questions = len(st.session_state.quiz_words)
            final_score = st.session_state.score
            percentage = (final_score / total_questions) * 100
            
            # Results header
            mode_name = "Find Translation" if st.session_state.game_mode == "translation" else "Find Definition"
            st.markdown(f"### 🎉 Quiz {mode_name} Terminé!")
            st.balloons()
            
            # Score display
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Score Final", f"{final_score}/{total_questions}")
            with col2:
                st.metric("Pourcentage", f"{percentage:.1f}%")
            with col3:
                if percentage >= 80:
                    st.metric("Résultat", "Excellent! 🏆")
                elif percentage >= 60:
                    st.metric("Résultat", "Bien! 👍")
                else:
                    st.metric("Résultat", "À améliorer 💪")
            
            # Results breakdown
            st.markdown("---")
            st.markdown("### 📋 Détail des réponses")
            
            for i, answer in enumerate(st.session_state.user_answers):
                with st.expander(f"Question {i+1}: {answer['word']} - {'✅' if answer['is_correct'] else '❌'}", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Mot:** {answer['word']}")
                        st.markdown(f"**Votre réponse:** {answer['selected']}")
                        st.markdown(f"**Bonne réponse:** {answer['correct']}")
                    with col2:
                        if answer['is_correct']:
                            st.success("✅ Correct!")
                        else:
                            st.error("❌ Incorrect")
            
            # Action buttons
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🔄 Nouvelle Partie", type="primary", use_container_width=True):
                    if start_new_game():
                        st.rerun()
            
            with col2:
                if st.button("🎯 Choix du mode", use_container_width=True):
                    # Réinitialiser l'état du jeu pour revenir au choix du mode
                    st.session_state.game_active = False
                    st.session_state.game_completed = False
                    st.session_state.current_question = 0
                    st.session_state.score = 0
                    st.session_state.quiz_words = []
                    st.session_state.user_answers = []
                    st.session_state.game_mode = None
                    st.rerun()

            with col3:
                if st.button("📊 Voir Statistiques", use_container_width=True):
                    st.switch_page("pages/3_📊_Stats.py")

            with col4:
                if st.button("🏠 Retour Accueil", use_container_width=True):
                    st.switch_page("app.py")
        
    except Exception as e:
        st.error(f"Erreur dans le jeu: {str(e)}")

if __name__ == "__main__":
    main()
