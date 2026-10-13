import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from utils.firebase_simple_config import FirebaseSimpleManager
from utils.firebase_auth import init_auth_session, is_authenticated, get_current_user, logout_user, current_user

# Page configuration
st.set_page_config(
    page_title="Stats - VocabMaster",
    page_icon="📊",
    layout="wide"
)

# Initialize authentication
init_auth_session()

# Check authentication
if not is_authenticated():
    st.warning("Vous devez vous connecter pour voir vos statistiques.")
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

def create_progress_chart(monthly_data):
    """Create monthly progress chart"""
    if not monthly_data:
        return None
    
    df = pd.DataFrame(monthly_data)
    
    fig = px.line(
        df, 
        x='month', 
        y='count',
        title='📈 Progression Mensuelle - Nouveaux Mots',
        labels={'month': 'Mois', 'count': 'Nombre de mots ajoutés'},
        markers=True
    )
    
    fig.update_layout(
        xaxis_title="Mois",
        yaxis_title="Nouveaux mots",
        hovermode='x unified'
    )
    
    return fig

def get_days_learning(words):
    """Number of days since the first word was added (at least 1)"""
    dates = []
    for word in words:
        try:
            dates.append(datetime.fromisoformat(word['created_at']))
        except (KeyError, TypeError, ValueError):
            continue
    if not dates:
        return 1
    return max((datetime.now() - min(dates)).days + 1, 1)

def main():
    st.title("📊 Stats - Statistiques d'Apprentissage")
    st.markdown("Suivez votre progression et vos performances")
    
    try:
        # Get statistics
        words = firebase_manager.get_all_words()
        total_words = len(words)
        game_stats = firebase_manager.get_game_stats()
        monthly_data = firebase_manager.get_monthly_progress(words)
        
        # Overview metrics
        st.markdown("### 📈 Vue d'ensemble")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📚 Mots enregistrés",
                value=total_words,
                delta=None
            )
        
        with col2:
            st.metric(
                label="🎮 Parties jouées",
                value=game_stats['total_games'],
                delta=None
            )
        
        with col3:
            best_score = game_stats['best_score']
            st.metric(
                label="🏆 Meilleur score",
                value=f"{best_score:.1f}%" if best_score else "N/A",
                delta=None
            )
        
        with col4:
            avg_score = game_stats['average_score']
            st.metric(
                label="📊 Score moyen",
                value=f"{avg_score:.1f}%" if avg_score else "N/A",
                delta=None
            )
        
        # Detailed statistics
        st.markdown("---")
        
        # Two columns layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📅 Progression Mensuelle")
            
            if monthly_data:
                # Monthly progress chart
                progress_chart = create_progress_chart(monthly_data)
                if progress_chart:
                    st.plotly_chart(progress_chart, use_container_width=True)
                
                # Monthly data table
                st.markdown("#### 📋 Détail mensuel")
                df_monthly = pd.DataFrame(monthly_data)
                if not df_monthly.empty:
                    df_monthly = df_monthly.rename(columns={'month': 'Mois', 'count': 'Nouveaux mots'})
                    st.dataframe(df_monthly, use_container_width=True, hide_index=True)
            else:
                st.info("Pas encore de données de progression mensuelle.")
        
        with col2:
            st.markdown("### 🎯 Performance des Quiz")
            
            if game_stats['total_games'] > 0:
                # Performance metrics
                st.markdown("#### 🏅 Métriques de performance")
                
                performance_data = {
                    'Métrique': ['Parties jouées', 'Score moyen', 'Meilleur score'],
                    'Valeur': [
                        str(game_stats['total_games']),
                        f"{game_stats['average_score']:.1f}%",
                        f"{game_stats['best_score']:.1f}%"
                    ]
                }
                
                df_performance = pd.DataFrame(performance_data)
                st.dataframe(df_performance, use_container_width=True, hide_index=True)
                
                # Performance level
                avg_score = game_stats['average_score']
                if avg_score >= 90:
                    st.success("🏆 Niveau: Expert!")
                elif avg_score >= 80:
                    st.success("🥇 Niveau: Avancé")
                elif avg_score >= 70:
                    st.info("🥈 Niveau: Intermédiaire")
                elif avg_score >= 60:
                    st.warning("🥉 Niveau: Débutant")
                else:
                    st.error("💪 Niveau: À améliorer")
                
            else:
                st.info("Aucune partie jouée pour le moment.")
                if st.button("🎮 Commencer un Quiz", type="primary"):
                    if total_words >= 15:
                        st.switch_page("pages/2_🎮_Game.py")
                    else:
                        st.warning(f"Il vous faut au moins 15 mots pour jouer. Vous en avez {total_words}.")
        
        # Learning insights
        st.markdown("---")
        st.markdown("### 💡 Insights d'Apprentissage")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📚 Statistiques de Vocabulaire")
            
            if total_words > 0:
                # Daily average since the first word was added
                days_learning = get_days_learning(words)
                daily_avg = total_words / days_learning
                
                vocab_insights = [
                    f"🎯 Objectif recommandé: 5 nouveaux mots par jour",
                    f"📊 Votre moyenne: {daily_avg:.1f} mots par jour",
                    f"💪 Progression: {'Excellent!' if daily_avg >= 5 else 'Continuez vos efforts!'}"
                ]
                
                for insight in vocab_insights:
                    st.markdown(f"• {insight}")
            else:
                st.info("Commencez par ajouter des mots pour voir vos statistiques!")
        
        with col2:
            st.markdown("#### 🎮 Recommandations de Jeu")
            
            if game_stats['total_games'] > 0:
                avg_score = game_stats['average_score']
                
                if avg_score >= 85:
                    recommendations = [
                        "🏆 Excellent travail! Continuez ainsi",
                        "📚 Ajoutez plus de mots pour maintenir le défi",
                        "🎯 Essayez de battre votre record!"
                    ]
                elif avg_score >= 70:
                    recommendations = [
                        "👍 Bon travail! Révisez vos mots difficiles",
                        "🔄 Rejouez pour améliorer votre score",
                        "📖 Concentrez-vous sur les définitions"
                    ]
                else:
                    recommendations = [
                        "💪 Continuez à pratiquer!",
                        "📚 Révisez vos mots dans 'My Words'",
                        "🎯 Fixez-vous un objectif de 70%"
                    ]
                
                for rec in recommendations:
                    st.markdown(f"• {rec}")
            else:
                st.info("Jouez votre première partie pour recevoir des recommandations!")
        
        # Quick actions
        st.markdown("---")
        st.markdown("### ⚡ Actions Rapides")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🏠 Accueil", use_container_width=True):
                st.switch_page("app.py")
        
        with col2:
            if st.button("📝 Mes Mots", use_container_width=True):
                st.switch_page("pages/1_📝_My_Words.py")

        with col3:
            if st.button("🎮 Jouer", use_container_width=True):
                if total_words >= 15:
                    st.switch_page("pages/2_🎮_Game.py")
                else:
                    st.warning(f"Il vous faut au moins 15 mots. Vous en avez {total_words}.")
        
        with col4:
            if st.button("🔄 Actualiser", use_container_width=True):
                st.cache_resource.clear()
                st.rerun()
        
        # Footer info
        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center; color: #666; font-size: 0.8em;'>
            📊 Statistiques mises à jour en temps réel • VocabMaster
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des statistiques: {str(e)}")
        st.markdown("Veuillez vérifier votre connexion et réessayer.")
        
        if st.button("🔄 Réessayer"):
            st.rerun()

if __name__ == "__main__":
    main()
