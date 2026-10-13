# VocabMaster

## Overview

VocabMaster is a smart English vocabulary learning app powered by AI. Simply enter any English word or phrase VocabMaster instantly provides clear French translations, definitions, and real-life usage examples. Build your own personal dictionary, play interactive word games, and watch your progress grow with easy-to-read stats. Everything is designed to make learning English simple, engaging, and effective.

![Home UI](/attached_assets/Home_UI.png)

## System Architecture

### Frontend Architecture

- **Framework**: Streamlit web application
- **Layout**: Multi-page application with wide layout configuration
- **Navigation**: Home page plus five pages (Login, My Words, Game, Stats, Learn)
- **UI Components**: Text inputs, buttons, tables, audio players, charts
- **Styling**: Custom CSS through Streamlit configuration

### Backend Architecture

- **Runtime**: Python 3.11
- **Application Structure**: Modular design with utilities separated into `utils/` directory
- **Session Management**: Streamlit session state for maintaining user interactions
- **Error Handling**: Try-catch blocks with user-friendly error messages in French

### Core Services

1. **AI Service** (`utils/ai_service.py`): OpenAI API integration (`gpt-6-luna`) for content generation
2. **Audio Service** (`utils/audio_service.py`): Text-to-speech using Google TTS (gTTS)
3. **Firebase Services** (`utils/firebase_auth.py`, `utils/firebase_simple_config.py`): Authentication and Realtime Database persistence via the Firebase REST APIs

## Key Components

### Main Application (`app.py`)

- Entry point for the vocabulary input interface
- Handles word validation and AI content generation
- Manages session state for user interactions
- Integrates with Firebase for data persistence

### Page Components

- **Login** (`pages/0_🔐_Login.py`): Sign in, sign up and password reset.

- **My Words** (`pages/1_📝_My_Words.py`): Personal dictionary management with search functionality.  
  ![My Words UI](/attached_assets/Words_UI.png)

- **Game** (`pages/2_🎮_Game.py`): Interactive vocabulary quiz with multiple choice questions (10 questions, requires at least 15 saved words)  
  ![Game UI](/attached_assets/Game_UI.png)

- **Stats** (`pages/3_📊_Stats.py`): Learning progress visualization using Plotly charts  
  ![Stats UI](/attached_assets/Stats_UI.png)

- **Learn** (`pages/4_📖_Learn.py`): AI word suggestions by level and theme, filtered against your saved words

### Utility Services

- **AI Integration**: Uses the OpenAI `gpt-6-luna` model (JSON mode) for generating definitions, examples and word suggestions
- **Audio Generation**: gTTS for pronunciation support
- **Database Management**: Firebase Realtime Database for persistent storage

## Data Flow

1. **Word Input**: User enters English word/expression on home page
2. **AI Processing**: OpenAI API generates definition, translation, and examples
3. **Content Display**: Generated content displayed with audio playback options
4. **Data Persistence**: User can save words to Firebase database
5. **Retrieval**: Saved words accessible through My Words page
6. **Gamification**: Quiz system uses saved words for interactive learning
7. **Analytics**: Stats page visualizes learning progress over time

## External Dependencies

### Core Dependencies

- `streamlit>=1.46.0`: Web application framework
- `requests>=2.32.4`: HTTP client for API communications
- `gtts>=2.5.4`: Google Text-to-Speech for audio generation
- `pandas>=2.3.0`: Data manipulation for statistics
- `plotly>=6.1.2`: Interactive charts and visualizations
- `openai>=1.40.0`: OpenAI API client
- `streamlit-searchbox`: Search bar with clickable suggestions
- `python-dotenv`: Loads environment variables from `.env`

### API Integrations

- **OpenAI API**: AI content generation using the `gpt-6-luna` model
- **Datamuse API**: Autocomplete suggestions (typo-tolerant) while typing a word on the home page
- **Firebase Auth**: Email/password authentication
- **Firebase Realtime Database**: Cloud database for user data storage
- **Google Text-to-Speech**: Audio generation service

### Environment Variables Required

- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_MODEL` (optional): model to use, defaults to `gpt-6-luna`
- `FIREBASE_API_KEY`: Firebase Web API key (authentication)
- `FIREBASE_DATABASE_URL`: Firebase Realtime Database URL

### Firebase Database Rules

Words and game results are queried per user with `orderBy="user_id"`. Add an index on both nodes so the filtering happens server-side:

```json
"words": { ".indexOn": ["user_id"] },
"game_results": { ".indexOn": ["user_id"] }
```

## Deployment Strategy

### Platform Configuration

- **Runtime**: Python 3.11
- **Port**: Application runs on port 5000
- **Command**: `streamlit run app.py --server.port 5000`

### Try the app : [https://eng-vocabmaster.streamlit.app/](https://eng-vocabmaster.streamlit.app/)
