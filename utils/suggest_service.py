import requests
import streamlit as st

# Datamuse autocomplete API (free, no key) - tolerant to spelling mistakes
DATAMUSE_SUGGEST_URL = "https://api.datamuse.com/sug"


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def _fetch_suggestions(term, max_results):
    response = requests.get(
        DATAMUSE_SUGGEST_URL,
        params={"s": term, "max": max_results},
        timeout=2,
    )
    response.raise_for_status()
    return [item["word"] for item in response.json() if item.get("word")]


def suggest_words(searchterm, max_results=8):
    """
    Return English words or expressions matching what the user is typing.
    Used as the search function of the home page searchbox.
    """
    term = (searchterm or "").strip().lower()
    if len(term) < 2:
        return []

    try:
        return _fetch_suggestions(term, max_results)
    except Exception as e:
        print(f"Erreur lors de la récupération des suggestions : {str(e)}")
        return []
