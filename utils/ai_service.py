import requests
import json
import os
import re
import streamlit as st
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()
# Ensure the Hugging Face token is set
HF_TOKEN = os.getenv('HUGGINGFACE_TOKEN', '').strip()   

# Initialize 
client = InferenceClient(
    model="HuggingFaceH4/zephyr-7b-beta",
    api_key=HF_TOKEN  # ou api_key=HF_TOKEN si version plus récente de huggingface_hub
)

def get_definition_and_examples(word):
    """ Get definition, translation, and examples for an English word using Mistral-Nemo-Instruct-2407
    """
    if not HF_TOKEN:
        print("Token Hugging Face manquant. Veuillez configurer votre clé API.")
        return create_fallback_response(word)
    
    messages = [
        {"role": "system", "content": "You are an English assistant."},
        {"role": "user", "content": (
            f'Provide a definition, French translation, and two English example sentences for the word '
            f'{word}. Format as JSON with keys: word, definition, translation, example1, example2.'
        )}
    ]

    try:
        response = client.chat.completions.create(
            model="HuggingFaceH4/zephyr-7b-beta",
            messages=messages,
            max_tokens=300,
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
