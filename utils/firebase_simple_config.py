import streamlit as st
import requests
import json
import os
from datetime import datetime
import uuid
from .env_loader import FIREBASE_DATABASE_URL
from .firebase_auth import get_current_user

class FirebaseSimpleManager:
    def __init__(self):
        self.database_url = FIREBASE_DATABASE_URL.rstrip('/')
    
    def add_word(self, word_data):
        """Add a new word to the database"""
        try:
            # Check if word already exists
            existing_words = self.get_all_words()
            for word in existing_words:
                if word.get('word', '').lower() == word_data.get('word', '').lower():
                    st.warning("Ce mot existe déjà dans votre collection!")
                    return False
            
            # Prepare word document
            word_doc = {
                'word': word_data.get('word', ''),
                'translation': word_data.get('translation', ''),
                'definition': word_data.get('definition', ''),
                'example1': word_data.get('example1', ''),
                'example2': word_data.get('example2', ''),
                'created_at': datetime.now().isoformat(),
                'id': str(uuid.uuid4())
            }
            
            # Send POST request to Firebase
            response = requests.post(f"{self.database_url}/words.json", json=word_doc)
            
            if response.status_code == 200:
                return True
            else:
                st.error(f"Erreur lors de l'ajout: {response.status_code}")
                return False
            
        except Exception as e:
            st.error(f"Erreur lors de l'ajout du mot: {str(e)}")
            return False
    
    def get_all_words(self):
        """Retrieve all words from the database"""
        try:
            response = requests.get(f"{self.database_url}/words.json")
            
            if response.status_code == 200:
                words_data = response.json() or {}
                word_list = []
                
                for key, word_data in words_data.items():
                    word_data['firebase_key'] = key
                    # Convert ISO string back to datetime for compatibility
                    if 'created_at' in word_data and isinstance(word_data['created_at'], str):
                        try:
                            word_data['created_at'] = datetime.fromisoformat(word_data['created_at'].replace('Z', '+00:00'))
                        except:
                            word_data['created_at'] = datetime.now()
                    word_list.append(word_data)
                
                # Sort by creation date (newest first)
                word_list.sort(key=lambda x: x.get('created_at', datetime.now()), reverse=True)
                return word_list
            else:
                return []
            
        except Exception as e:
            st.error(f"Erreur lors de la récupération des mots: {str(e)}")
            return []
    
    def get_random_words(self, count=10):
        """Get random words for quiz"""
        try:
            all_words = self.get_all_words()
            if len(all_words) < count:
                return all_words
            
            import random
            return random.sample(all_words, count)
            
        except Exception as e:
            st.error(f"Erreur lors de la sélection aléatoire: {str(e)}")
            return []
    
    def save_game_result(self, score, total_questions):
        """Save game result to database"""
        try:
            game_doc = {
                'score': score,
                'total_questions': total_questions,
                'percentage': (score / total_questions) * 100,
                'played_at': datetime.now().isoformat(),
                'id': str(uuid.uuid4())
            }
            
            response = requests.post(f"{self.database_url}/game_results.json", json=game_doc)
            
            if response.status_code == 200:
                return True
            else:
                st.error(f"Erreur lors de la sauvegarde: {response.status_code}")
                return False
            
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde du score: {str(e)}")
            return False
    
    def get_game_stats(self):
        """Get game statistics"""
        try:
            response = requests.get(f"{self.database_url}/game_results.json")
            
            if response.status_code == 200:
                games_data = response.json() or {}
                
                if not games_data:
                    return {'total_games': 0, 'best_score': 0, 'average_score': 0}
                
                scores = [game['percentage'] for game in games_data.values() if 'percentage' in game]
                
                if not scores:
                    return {'total_games': 0, 'best_score': 0, 'average_score': 0}
                
                return {
                    'total_games': len(scores),
                    'best_score': max(scores),
                    'average_score': sum(scores) / len(scores)
                }
            else:
                return {'total_games': 0, 'best_score': 0, 'average_score': 0}
            
        except Exception as e:
            st.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            return {'total_games': 0, 'best_score': 0, 'average_score': 0}
    
    def get_total_words_count(self):
        """Get total number of words"""
        try:
            words = self.get_all_words()
            return len(words)
        except:
            return 0
    
    def get_total_games_count(self):
        """Get total number of games played"""
        try:
            stats = self.get_game_stats()
            return stats['total_games']
        except:
            return 0
    
    def get_best_score(self):
        """Get best score"""
        try:
            stats = self.get_game_stats()
            return round(stats['best_score'], 1) if stats['best_score'] else None
        except:
            return None
    
    def get_monthly_progress(self):
        """Get monthly learning progress"""
        try:
            words = self.get_all_words()
            monthly_data = {}
            
            for word_data in words:
                if 'created_at' in word_data:
                    try:
                        if isinstance(word_data['created_at'], str):
                            created_at = datetime.fromisoformat(word_data['created_at'].replace('Z', '+00:00'))
                        else:
                            created_at = word_data['created_at']
                        
                        month_key = f"{created_at.year}-{created_at.month:02d}"
                        month_name = f"{created_at.strftime('%B')} {created_at.year}"
                        
                        if month_key not in monthly_data:
                            monthly_data[month_key] = {'month': month_name, 'count': 0}
                        monthly_data[month_key]['count'] += 1
                    except:
                        continue
            
            # Sort by date and return
            sorted_data = sorted(monthly_data.values(), key=lambda x: x['month'])
            return sorted_data
            
        except Exception as e:
            st.error(f"Erreur lors de la récupération des données mensuelles: {str(e)}")
            return []