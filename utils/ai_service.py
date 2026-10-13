import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
# Ensure the OpenAI key is set
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip()
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-6-luna').strip()

# Initialize
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def _chat_json(system_prompt, user_prompt):
    """Call the OpenAI model and return its answer parsed as a JSON object"""
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def get_definition_and_examples(word):
    """ Get definition, translation, and examples for an English word using OpenAI
    """
    if not client:
        print("Clé OpenAI manquante. Veuillez configurer OPENAI_API_KEY.")
        return create_fallback_response(word)

    try:
        data = _chat_json(
            "You are an English assistant. Always answer with a JSON object only.",
            f'Provide a definition, French translation, and two English example sentences for the word '
            f'"{word}". The two examples should contain the word in different contexts and always be in English. '
            f'Format the response as JSON with keys: word, definition, translation, example1, example2.'
        )
        if validate_word_data(data):
            return {field: str(data[field]).strip() for field in REQUIRED_FIELDS}
        print(f"Réponse incomplète du modèle : {data}")
        return create_fallback_response(word)

    except Exception as e:
        print(f"Erreur lors de l'appel au modèle : {str(e)}")
        return create_fallback_response(word)


def get_word_suggestions(count, focus):
    """
    Ask the model for `count` English words or expressions to learn.
    Raises on API errors so the caller can choose a fallback.
    """
    if not client:
        raise RuntimeError("Clé OpenAI manquante. Veuillez configurer OPENAI_API_KEY.")

    data = _chat_json(
        "You are a helpful English vocabulary teacher. Always answer with a JSON object only.",
        f"""Generate exactly {count} English words or short expressions for language learners.

    Focus on: {focus}

    Requirements:
    - Return a JSON object with a single key "words" containing the list
    - Format: {{"words": ["word1", "phrase2", "word3", ...]}}
    - Avoid basic words like: hello, yes, no, please, thank you
    - Include a mix of single words and short phrases
    - Make them useful for vocabulary learning

    Example: {{"words": ["serendipity", "break the ice", "procrastinate", "state of the art", "mindset"]}}"""
    )
    words = data.get("words", [])
    return [str(w) for w in words] if isinstance(words, list) else []


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


REQUIRED_FIELDS = ['word', 'definition', 'translation', 'example1', 'example2']


def validate_word_data(word_data):
    """
    Validate that word data contains all required fields
    """
    return isinstance(word_data, dict) and all(word_data.get(field) for field in REQUIRED_FIELDS)
