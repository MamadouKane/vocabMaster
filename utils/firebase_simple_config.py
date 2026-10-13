from datetime import datetime
import json
import os
import time
import requests
import uuid
import streamlit as st
from dotenv import load_dotenv
from .firebase_auth import get_current_user, FirebaseAuth, set_token_expiry

# Load environment variables
load_dotenv()
FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')

class FirebaseSimpleManager:
    def __init__(self):
        self.database_url = FIREBASE_DATABASE_URL.rstrip('/')
        self._auth = FirebaseAuth()

    def _get_token(self):
        """Return a valid ID token, refreshing it if necessary."""
        token = st.session_state.get('auth_token')
        if not token:
            return None

        # Reuse the token until one minute before it expires
        if time.time() < st.session_state.get('token_expires_at', 0) - 60:
            return token

        # Token expired — attempt refresh
        refresh_tok = st.session_state.get('refresh_token')
        if not refresh_tok:
            return None

        result = self._auth.refresh_token(refresh_tok)
        if result.get('success'):
            st.session_state.auth_token = result['token']
            st.session_state.refresh_token = result['refresh_token']
            set_token_expiry(result.get('expires_in'))
            return result['token']

        return None

    def _url(self, path):
        """Build an authenticated Firebase REST URL."""
        token = self._get_token()
        auth_param = f"?auth={token}" if token else ""
        return f"{self.database_url}/{path}.json{auth_param}"

    def _get_user_records(self, path, user_id):
        """Fetch only the current user's records under `path`.

        Filters server-side with orderBy/equalTo, which requires
        ".indexOn": ["user_id"] on `path` in the database rules.
        Falls back to client-side filtering if the index is missing.
        """
        params = {'orderBy': '"user_id"', 'equalTo': json.dumps(user_id)}
        response = requests.get(self._url(path), params=params)
        if response.status_code == 400 and 'index' in response.text.lower():
            response = requests.get(self._url(path))
        if response.status_code != 200:
            return None, response.status_code
        records = response.json() or {}
        return [r for r in records.values() if r.get('user_id') == user_id], 200

    def add_word(self, word_data):
        """Add a new word to the database for the current user"""
        try:
            user = get_current_user()
            if not user:
                st.error("Utilisateur non authentifié.")
                return False
            user_id = user.get('user_id') or user.get('email')
            if not user_id:
                st.error("Impossible de récupérer l'identifiant utilisateur.")
                return False

            # Check if word already exists for this user
            existing_words = self.get_all_words()
            for word in existing_words:
                if word.get('word', '').lower() == word_data.get('word', '').lower():
                    st.warning(f"Le mot '{word_data.get('word', '')}' existe déjà dans votre liste.")
                    return False

            # Prepare word document
            word_doc = {
                'word': word_data.get('word', ''),
                'translation': word_data.get('translation', ''),
                'definition': word_data.get('definition', ''),
                'example1': word_data.get('example1', ''),
                'example2': word_data.get('example2', ''),
                'created_at': datetime.now().isoformat(),
                'id': str(uuid.uuid4()),
                'user_id': user_id
            }

            # Send POST request to Firebase (authenticated)
            response = requests.post(self._url("words"), json=word_doc)

            if response.status_code == 200:
                return True
            else:
                st.error(f"Erreur lors de l'ajout: {response.status_code}")
                return False

        except Exception as e:
            st.error(f"Erreur lors de l'ajout du mot: {str(e)}")
            return False

    def get_all_words(self):
        """Retrieve all words for the current user from the database"""
        try:
            user = get_current_user()
            if not user:
                st.error("Utilisateur non authentifié.")
                return []
            user_id = user.get('user_id') or user.get('email')
            word_list, status = self._get_user_records("words", user_id)

            if word_list is not None:
                # Sort by creation date (newest first)
                word_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                return word_list
            else:
                st.error(f"Erreur lors de la récupération des mots: {status}")
                return []
        except Exception as e:
            st.error(f"Erreur lors de la récupération des mots: {str(e)}")
            return []

    def get_random_words(self, count=10):
        """Get random words for quiz (for current user)"""
        import random
        try:
            all_words = self.get_all_words()
            if len(all_words) < count:
                st.warning(f"Vous n'avez pas assez de mots pour jouer (minimum {count}).")
                return []
            return random.sample(all_words, count)
        except Exception as e:
            st.error(f"Erreur lors de la sélection aléatoire: {str(e)}")
            return []

    def save_game_result(self, score, total_questions):
        """Save game result to database for current user"""
        try:
            user = get_current_user()
            if not user:
                st.error("Utilisateur non authentifié.")
                return False
            user_id = user.get('user_id') or user.get('email')
            game_doc = {
                'score': score,
                'total_questions': total_questions,
                'percentage': (score / total_questions) * 100,
                'played_at': datetime.now().isoformat(),
                'id': str(uuid.uuid4()),
                'user_id': user_id
            }
            response = requests.post(self._url("game_results"), json=game_doc)
            if response.status_code == 200:
                return True
            else:
                st.error(f"Erreur lors de la sauvegarde du score: {response.status_code}")
                return False
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde du score: {str(e)}")
            return False

    def get_game_stats(self):
        """Get game statistics for current user"""
        try:
            user = get_current_user()
            if not user:
                st.error("Utilisateur non authentifié.")
                return {'total_games': 0, 'best_score': 0, 'average_score': 0}
            user_id = user.get('user_id') or user.get('email')
            user_results, status = self._get_user_records("game_results", user_id)
            if user_results is not None:
                total_games = len(user_results)
                best_score = max([r.get('percentage', 0) for r in user_results], default=0)
                average_score = sum([r.get('percentage', 0) for r in user_results]) / total_games if total_games > 0 else 0
                return {
                    'total_games': total_games,
                    'best_score': best_score,
                    'average_score': average_score
                }
            else:
                st.error(f"Erreur lors de la récupération des statistiques: {status}")
                return {'total_games': 0, 'best_score': 0, 'average_score': 0}
        except Exception as e:
            st.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            return {'total_games': 0, 'best_score': 0, 'average_score': 0}

    def get_total_words_count(self):
        """Get total number of words for current user"""
        try:
            words = self.get_all_words()
            return len(words)
        except:
            return 0

    def get_total_games_count(self):
        """Get total number of games played for current user"""
        try:
            stats = self.get_game_stats()
            return stats['total_games']
        except:
            return 0

    def get_best_score(self):
        """Get best score for current user"""
        try:
            stats = self.get_game_stats()
            return round(stats['best_score'], 1) if stats['best_score'] else None
        except:
            return None

    def get_monthly_progress(self, words=None):
        """Get monthly learning progress for current user"""
        try:
            if words is None:
                words = self.get_all_words()
            monthly_data = {}
            for word_data in words:
                if 'created_at' in word_data:
                    month = word_data['created_at'][:7]  # YYYY-MM
                    if month not in monthly_data:
                        monthly_data[month] = {'month': month, 'count': 0}
                    monthly_data[month]['count'] += 1
            # Sort by date and return
            sorted_data = sorted(monthly_data.values(), key=lambda x: x['month'])
            return sorted_data
        except Exception as e:
            st.error(f"Erreur lors de la récupération des données mensuelles: {str(e)}")
            return []