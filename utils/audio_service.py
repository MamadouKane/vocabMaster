import streamlit as st
from gtts import gTTS
import io
import base64
import os
import tempfile

def text_to_speech(text, lang='en'):
    """
    Convert text to speech using gTTS
    """
    try:
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            # Generate speech
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(tmp_file.name)
            
            # Read the audio file
            with open(tmp_file.name, 'rb') as audio_file:
                audio_bytes = audio_file.read()
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
            
            return audio_bytes
            
    except Exception as e:
        st.error(f"Erreur lors de la génération audio: {str(e)}")
        return None

def play_audio_button(text, key, lang='en'):
    """
    Create an audio play button for given text with better styling
    """
    try:
        # Create audio button with custom styling
        if st.button("▶️", key=f"audio_{key}", help=f"Écouter: {text[:50]}...", 
                     type="secondary", use_container_width=False):
            # Generate audio
            audio_bytes = text_to_speech(text, lang)
            
            if audio_bytes:
                # Create audio player
                st.audio(audio_bytes, format='audio/mp3')
            else:
                st.error("Impossible de générer l'audio pour ce texte.")
                
    except Exception as e:
        st.error(f"Erreur audio: {str(e)}")

def play_audio_inline(text, key, lang='en'):
    """
    Create an inline audio button that aligns with content
    """
    try:
        # Use columns to align audio button with text
        col1, col2 = st.columns([0.9, 0.1])
        
        with col1:
            # Content is displayed by the caller
            pass
        
        with col2:
            if st.button("🎵", key=f"audio_{key}", help=f"Écouter: {text[:30]}...",
                        type="secondary", use_container_width=True):
                # Generate audio
                audio_bytes = text_to_speech(text, lang)
                
                if audio_bytes:
                    # Create audio player
                    st.audio(audio_bytes, format='audio/mp3')
                else:
                    st.error("Impossible de générer l'audio pour ce texte.")
                    
    except Exception as e:
        st.error(f"Erreur audio: {str(e)}")

def create_content_with_audio(content_text, audio_text, key, lang='en', content_type="text"):
    """
    Create content with inline audio button and full-width audio player
    """
    # Initialize session state for this audio key
    if f"show_audio_{key}" not in st.session_state:
        st.session_state[f"show_audio_{key}"] = False
    
    col1, col2 = st.columns([0.85, 0.15])
    
    with col1:
        if content_type == "markdown":
            st.markdown(content_text.replace('": "', '').replace('",', ''))
        else:
            st.write(content_text.replace('": "', '').replace('",', ''))
    
    with col2:
        if st.button("🎧", key=f"audio_{key}", help=f"Écouter: {audio_text[:30]}...",
                    type="secondary", use_container_width=True):
            st.session_state[f"show_audio_{key}"] = True
    
    # Show audio player in full width if requested
    if st.session_state[f"show_audio_{key}"]:
        try:
            audio_bytes = text_to_speech(audio_text, lang)
            if audio_bytes:
                st.audio(audio_bytes, format='audio/mp3')
                # Reset the state so it doesn't keep showing
                st.session_state[f"show_audio_{key}"] = False
            else:
                st.error("Impossible de générer l'audio pour ce texte.")
        except Exception as e:
            st.error(f"Erreur audio: {str(e)}")

def create_audio_html(text, lang='en'):
    """
    Create HTML audio player (alternative approach)
    """
    try:
        audio_bytes = text_to_speech(text, lang)
        if audio_bytes:
            # Convert to base64 for HTML embedding
            audio_b64 = base64.b64encode(audio_bytes).decode()
            audio_html = f"""
            <audio controls style="width: 100px; height: 30px;">
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                Votre navigateur ne supporte pas l'audio HTML5.
            </audio>
            """
            return audio_html
        return None
    except Exception as e:
        print(f"Error creating audio HTML: {str(e)}")
        return None

@st.cache_data
def get_cached_audio(text, lang='en'):
    """
    Cache audio generation to improve performance
    """
    return text_to_speech(text, lang)
