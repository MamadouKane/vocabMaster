import requests
import json
import os
import re
import streamlit as st
from langdetect import detect, LangDetectException
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()
# Ensure the Hugging Face token is set
HF_TOKEN = os.getenv('HUGGINGFACE_TOKEN', '').strip()   

def is_english(text):
    """
    Check if the input text is in English
    Returns: bool, True if text is in English, False otherwise
    """
    try:
        return detect(text) == 'en'
    except LangDetectException:
        return False  # En cas d'erreur, on considère que ce n'est pas de l'anglais

# def get_definition_and_examples(word):
#     """
#     Get definition, translation, and examples for an English word using Hugging Face API
#     """
#     if not HF_TOKEN:
#         st.error("Token Hugging Face manquant. Veuillez configurer votre clé API.")
#         return create_fallback_response(word)
    
#     # Define API URL and headers
#     API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
#     headers = {
#         "Authorization": f"Bearer {HF_TOKEN}",
#         "Content-Type": "application/json"
#     }

#     # Structure the prompt - Modified to be more strict and direct
#     prompt = f"""
#         You are an English language assistant. 
#         Provide a definition, French translation, and two example sentences in English for the English word "{word}". 
#         Format your response as JSON with fields: word, definition, translation, example1, example2.
#     """
    
#     # Prepare payload
#     payload = {
#         "inputs": prompt,
#         "parameters": {
#             "temperature": 0.1,  # Reduced for more consistent responses
#             "max_new_tokens": 200,
#             "return_full_text": False  # Only return newly generated text
#         }
#     }
    
#     try:
#         # Send POST request
#         response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
#         # Check response status
#         if response.status_code == 200:
#             response_data = response.json()
#             generated_text = response_data[0]["generated_text"]
            
#             # Try to parse as JSON directly
#             if generated_text:
#                 try:
#                     return json.loads(generated_text)
#                 except json.JSONDecodeError:
#                     # Fallback: try to extract information manually
#                     return extract_info_manually(generated_text, word)
            
#             print("No valid content generated")
#             return create_fallback_response(word)
            
#         elif response.status_code == 503:
#             st.warning("Le modèle IA est en cours de chargement. Veuillez réessayer dans quelques secondes.")
#             return None
#         elif response.status_code == 401:
#             st.error("Erreur d'authentification: Vérifiez votre token Hugging Face.")
#             return None
#         else:
#             print(f"Hugging Face API Error: {response.status_code} -> {response.text}")
#             return create_fallback_response(word)
            
#     except requests.exceptions.Timeout:
#         st.error("Timeout: La requête a pris trop de temps. Veuillez réessayer.")
#         return None
#     except requests.exceptions.RequestException as e:
#         st.error(f"Erreur de connexion: {str(e)}")
#         return None
#     except Exception as e:
#         print(f"Unexpected error: {str(e)}")
#         return create_fallback_response(word)


# Initialise le client avec un modèle warm
client = InferenceClient(
    model="mistralai/Mistral-Nemo-Instruct-2407",
    token=HF_TOKEN  # ou api_key=HF_TOKEN si version plus récente de huggingface_hub
)

def get_definition_and_examples(word):
    """ Get definition, translation, and examples for an English word using Mistral-Nemo-Instruct-2407
    """
    # Vérifier si le mot est en anglais
    if not is_english(word):
        st.error("Veuillez entrer un mot ou une expression correcte en anglais.")
        # return create_fallback_response(word)
        return None
        
    # Check if the Hugging Face token is set    
    if not HF_TOKEN:
        print("Token Hugging Face manquant. Veuillez configurer votre clé API.")
        return create_fallback_response(word)
    
    messages = [
        {"role": "system", "content": "You are an English assistant."},
        {"role": "user", "content": (
            f'Provide a definition, French translation, and two English example sentences for the word '
            f'"{word}". Format as JSON with keys: word, definition, translation, example1, example2.'
        )}
    ]

    try:
        response = client.chat.completions.create(
            model="mistralai/Mistral-Nemo-Instruct-2407",
            messages=messages,
            max_tokens=200,
            temperature=0.1,
        )
        text = response.choices[0].message.content

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return extract_info_manually(text, word)

    except Exception as e:
        print(f"Erreur lors de l'appel au modèle : {str(e)}")
        return create_fallback_response(word)



def extract_info_manually(text, word):
    """
    Extract information manually from generated text if JSON parsing fails
    """
    try:
        # Try to extract key information using regex
        definition_pattern = r'[Dd]efinition[:\s]*([^.\n]+)'
        translation_pattern = r'[Tt]ranslation[:\s]*([^.\n]+)'
        example_pattern = r'[Ee]xample[^:]*:[^"]*"([^"]+)"'
        
        definition_match = re.search(definition_pattern, text)
        translation_match = re.search(translation_pattern, text)
        example_matches = re.findall(example_pattern, text)
        
        result = {
            'word': word,
            'definition': definition_match.group(1).strip() if definition_match else f"Definition for {word}",
            'translation': translation_match.group(1).strip() if translation_match else f"Traduction de {word}",
            'example1': example_matches[0] if len(example_matches) > 0 else f"Example sentence with {word}.",
            'example2': example_matches[1] if len(example_matches) > 1 else f"Another example with {word}."
        }
        
        return result
        
    except Exception as e:
        print(f"Manual extraction failed: {str(e)}")
        return create_fallback_response(word)

def create_fallback_response(word):
    """
    Create a fallback response when AI generation fails
    """
    return {
        'word': word,
        'definition': f"Définition pour '{word}' - consultez un dictionnaire pour plus de détails.",
        'translation': f"Traduction de '{word}' non disponible.",
        'example1': f"Exemple d'utilisation de '{word}' non disponible.",
        'example2': f"Autre exemple avec '{word}' non disponible."
    }

def validate_word_data(word_data):
    """
    Validate that word data contains all required fields
    """
    required_fields = ['word', 'definition', 'translation', 'example1', 'example2']
    return all(field in word_data and word_data[field] for field in required_fields)
