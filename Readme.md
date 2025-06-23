# VocabMaster - Replit Configuration Guide

## Overview

VocabMaster is a smart English vocabulary learning app powered by AI. Simply enter any English word or phrase VocabMaster instantly provides clear French translations, definitions, and real-life usage examples. Build your own personal dictionary, play interactive word games, and watch your progress grow with easy-to-read stats. Everything is designed to make learning English simple, engaging, and effective.

## System Architecture

### Frontend Architecture

- **Framework**: Streamlit web application
- **Layout**: Multi-page application with wide layout configuration
- **Navigation**: Four main pages (Home, My Words, Game, Stats)
- **UI Components**: Text inputs, buttons, tables, audio players, charts
- **Styling**: Custom CSS through Streamlit configuration

### Backend Architecture

- **Runtime**: Python 3.11
- **Application Structure**: Modular design with utilities separated into `utils/` directory
- **Session Management**: Streamlit session state for maintaining user interactions
- **Error Handling**: Try-catch blocks with user-friendly error messages in French

### Core Services

1. **AI Service** (`utils/ai_service.py`): Hugging Face API integration for content generation
2. **Audio Service** (`utils/audio_service.py`): Text-to-speech using Google TTS (gTTS)
3. **Firebase Service** (`utils/firebase_config.py`): Database management and user data persistence

## Key Components

### Main Application (`app.py`)

- Entry point for the vocabulary input interface
- Handles word validation and AI content generation
- Manages session state for user interactions
- Integrates with Firebase for data persistence

### Page Components

- **Login** (`pages/0_login.py`): Login page
- **My Words** (`pages/1_My_Words.py`): Personal dictionary management with search functionality
- **Game** (`pages/2_Game.py`): Interactive vocabulary quiz with multiple choice questions
- **Stats** (`pages/3_Stats.py`): Learning progress visualization using Plotly charts

### Utility Services

- **AI Integration**: Uses Hugging Face Zephyr-7B model for generating definitions and examples
- **Audio Generation**: gTTS for pronunciation support
- **Database Management**: Firebase Firestore for persistent storage

## Data Flow

1. **Word Input**: User enters English word/expression on home page
2. **AI Processing**: Hugging Face API generates definition, translation, and examples
3. **Content Display**: Generated content displayed with audio playback options
4. **Data Persistence**: User can save words to Firebase database
5. **Retrieval**: Saved words accessible through My Words page
6. **Gamification**: Quiz system uses saved words for interactive learning
7. **Analytics**: Stats page visualizes learning progress over time

## External Dependencies

### Core Dependencies

- `streamlit>=1.46.0`: Web application framework
- `firebase-admin>=6.9.0`: Firebase integration for data persistence
- `requests>=2.32.4`: HTTP client for API communications
- `gtts>=2.5.4`: Google Text-to-Speech for audio generation
- `pandas>=2.3.0`: Data manipulation for statistics
- `plotly>=6.1.2`: Interactive charts and visualizations

### API Integrations

- **Hugging Face Inference API**: AI content generation using Zephyr-7B model
- **Firebase Firestore**: Cloud database for user data storage
- **Google Text-to-Speech**: Audio generation service

### Environment Variables Required

- `HUGGINGFACE_TOKEN`: Authentication token for Hugging Face API
- `FIREBASE_CREDENTIALS`: JSON credentials for Firebase service account

## Deployment Strategy

### Platform Configuration

- **Runtime**: Python 3.11 with Nix package management
- **Port**: Application runs on port 5000
- **Command**: `streamlit run app.py --server.port 5000`
